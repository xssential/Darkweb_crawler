from elasticsearch import Elasticsearch
from geopy.geocoders import Nominatim
from datetime import *
import requests
import json
import pytz
import os

class ELK:
    def __init__(self):
        self.es = None
        self.INDEX_NAME = "RansomwareGroups".lower()
        self.KIBANA_URL = "http://kibana:5601"
        self.elasticsearch = "http://elasticsearch:9200"
        self.HEADERS = {"kbn-xsrf": "true", "Content-Type": "application/json"}
        self.panel_idx = 1

    def init_elk(self):
        self.es = Elasticsearch(self.elasticsearch)

    def geocoding(self, doc):
        tmp={}
        if doc['address']!='N/A':
            address=doc['address']
            geourl = "https://nominatim.openstreetmap.org/search"
            headers = {
                "User-Agent": "MyAppName/1.0 (contact: your_email@example.com)"
            }
            parts = [p.strip() for p in address.split(',')]

            if len(parts) < 3:
                try:
                    geolocoder = Nominatim(user_agent = doc['country'], timeout=None)
                    geo = geolocoder.geocode(address)
                    crd = {"lat": str(geo.latitude), "lon": str(geo.longitude)}
                except Exception as e:
                    geolocoder = Nominatim(user_agent = doc['country'], timeout=None)
                    if doc['region']=="N/A":
                        crd = {"lat": str(0.0), "lon": str(0.0)}   
                    else: 
                        geo = geolocoder.geocode(doc['region'])
                        crd = {"lat": str(geo.latitude), "lon": str(geo.longitude)}
                doc['region'] = crd
                return doc

            second_last = parts[-2] 
            third_last = parts[-3] 

            params = {
                "format": "json",
                "q": second_last
            }
            response = requests.get(geourl, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    geolocoder = Nominatim(user_agent = doc['country'], timeout=None)
                    if doc['region']=="N/A":
                        crd = {"lat": str(0.0), "lon": str(0.0)}   
                    else: 
                        geo = geolocoder.geocode(doc['region'])
                        crd = {"lat": str(geo.latitude), "lon": str(geo.longitude)}
                    tmp['region'] = crd
                else:
                    if len(data) == 1:
                        lat = data[0].get("lat", "0.0")
                        lon = data[0].get("lon", "0.0")
                        crd = {"lat": str(lat), "lon": str(lon)}
                    else:
                        filtered_results = [res for res in data if third_last in res.get("display_name", "")]

                        if not filtered_results:
                            pass
                        else:
                            for result in filtered_results:
                                lat = result.get("lat", "0.0")
                                lon = result.get("lon", "0.0")
                                crd = {"lat": str(lat), "lon": str(lon)}
                    tmp['region'] = crd

                if tmp['region']=={"lat": str(0.0), "lon": str(0.0)}:
                    geolocoder = Nominatim(user_agent = doc['country'], timeout=None)
                    if doc['region']=="N/A":
                        crd = {"lat": str(0.0), "lon": str(0.0)}   
                    else: 
                        geo = geolocoder.geocode(doc['region'])
                        crd = {"lat": str(geo.latitude), "lon": str(geo.longitude)}
                    tmp['region']=crd
            else:
                geolocoder = Nominatim(user_agent = doc['country'], timeout=None)
                if doc['region']=="N/A":
                    crd = {"lat": str(0.0), "lon": str(0.0)}   
                else: 
                    geo = geolocoder.geocode(doc['region'])
                    crd = {"lat": str(geo.latitude), "lon": str(geo.longitude)}
                tmp['region'] = crd
        
        else:
            geolocoder = Nominatim(user_agent = doc['country'], timeout=None)
            if doc['region']=="N/A":
                crd = {"lat": str(0.0), "lon": str(0.0)}   
            else: 
                geo = geolocoder.geocode(doc['region'])
                crd = {"lat": str(geo.latitude), "lon": str(geo.longitude)}
            tmp['region'] = crd
        doc['region']=tmp['region']
        return doc

    def create_mapping(self):
        mapping = {
            "mappings": {
                "properties": {
                    "title": {"type": "keyword"}, 
                    "Description": {"type": "text"},
                    "site": {"type": "keyword"}, 
                    "address": {"type": "text"}, 
                    "country": {"type": "keyword"}, 
                    "region": {"type": "geo_point"},
                    "all data": {"type": "text"},
                    "tel": {"type": "keyword"}, 
                    "link": {"type": "keyword"},
                    "images": {"type": "text"},
                    "attacker": {"type": "keyword"},
                    "@timestamp": {"type": "date"}
                }
            }
        }
        if not self.check_index_pattern():
            self.es.indices.create(index=self.INDEX_NAME, body=mapping)
            print(f"Index '{self.INDEX_NAME}' created with mapping.")
        else:
            print(f"Index '{self.INDEX_NAME}' already exists.")

    def delete_all_documents(self):
        try:
            response = self.es.delete_by_query(
                index=self.INDEX_NAME,
                body={
                    "query": {
                        "match_all": {}
                    }
                }
            )
            print(f"Deleted documents in index '{self.INDEX_NAME}': {response['deleted']} documents")
        except Exception as e:
            print(f"Error deleting documents: {e}")


    def upload_data_view(self):
        docs = {}

        path = "/app/OUT/"
        file_list = os.listdir(path)
        file_list_json = [file for file in file_list if file.endswith(".json")]

        for json_file in file_list_json:
            tmp={}
            with open(path+json_file) as f:
                tmp.update(json.load(f))
            attacker = json_file[:json_file.find('_')]
            for key, value in tmp.items():
                value.update({"attacker":attacker})
            if "N/A" in tmp:
                tmp.pop("N/A")
            docs.update(tmp)

        for index, doc in docs.items():
            doc = self.geocoding(doc)
            utc_now = datetime.now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            doc.update({"@timestamp": utc_now})

            self.es.index(index=self.INDEX_NAME, body=doc)


    def create_data_view(self):
        url = f"{self.KIBANA_URL}/api/data_views/data_view"
        payload = {
            "data_view": {
                "title": self.INDEX_NAME,
                "timeFieldName": "@timestamp"
            }
        }
        if self.check_data_view():
            self.delete_data_view()
        response = requests.post(url, headers=self.HEADERS, json=payload)
        if response.status_code == 200:
            print(f"Data View '{self.INDEX_NAME}' created successfully in Kibana.")
        else:
            print(f"Failed to create Data View: {response.status_code}, {response.text}")

    def get_index_pattern_id(self):
        url = f"{self.KIBANA_URL}/api/data_views"
        response = requests.get(url, headers=self.HEADERS)
        if response.status_code == 200:
            data_views = response.json()["data_view"]
            for view in data_views:
                if view["title"] == self.INDEX_NAME:
                    return view["id"]
        print(f"Data view '{self.INDEX_NAME}' not found.")
        return None

    def create_table_visualization(self,index_pattern_id):
        """
        선언 example
        create_table_visualization(get_index_pattern_id('blackbasta'), 'blackbasta')

        위 선언의 'blackbasta'부분은 INDEX_NAME으로 수정할 것

        """
        url = f"{self.KIBANA_URL}/api/saved_objects/visualization"
        payload = {
            "attributes": {
                "title": self.INDEX_NAME,
                "visState": json.dumps({
                    "title": self.INDEX_NAME,
                    "type": "table",
                    "params": {
                        "perPage": 10, 
                        "showMetricsAtAllLevels": False,
                        "showPartialRows": False,
                        "showTotal": False
                    },
                    "aggs": [
                        {
                            "id": "1",
                            "enabled": True,
                            "type": "terms",
                            "schema": "bucket",
                            "params": {
                                "field": "attacker",
                                "size": 500,
                                "order": {"type": "alphabetical", "direction": "desc"} 
                            }
                        },
                        {
                            "id": "2",
                            "enabled": True,
                            "type": "terms",
                            "schema": "bucket",
                            "params": {
                                "field": "title",
                                "size": 500,  
                                "order": {"type": "alphabetical", "direction": "desc"}  
                            }
                        },
                        {
                            "id": "3",
                            "enabled": True,
                            "type": "terms",
                            "schema": "bucket",
                            "params": {
                                "field": "country",
                                "size": 500,
                                "order": {"type": "alphabetical", "direction": "desc"}
                            }
                        },
                        {
                            "id": "4",
                            "enabled": True,
                            "type": "terms",
                            "schema": "bucket",
                            "params": {
                                "field": "site",
                                "size": 500,
                                "order": {"type": "alphabetical", "direction": "desc"}
                            }
                        },
                        {
                            "id": "5",
                            "enabled": True,
                            "type": "terms",
                            "schema": "bucket",
                            "params": {
                                "field": "link",
                                "size": 500,
                                "order": {"type": "alphabetical", "direction": "desc"}
                            }
                        }
                    ]
                }),
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": json.dumps({
                        "index": index_pattern_id,
                        "query": {"language": "kuery", "query": ""}, 
                        "filter": [] 
                    })
                }
            }
        }
        if self.check_visualization():
            self.delete_visualization()
        response = requests.post(url, headers=self.HEADERS, json=payload)
        if response.status_code == 200:
            visualization_id = response.json()["id"]
            print(f"Table visualization '{self.INDEX_NAME}' created successfully with ID: {visualization_id}")
            return visualization_id, 'visualization'
        else:
            print(f"Failed to create Table visualization: {response.status_code}, {response.text}")
            return None, None


    def create_map_with_es_layer(self,data_view_id, geo_field='region'):
        url = f"{self.KIBANA_URL}/api/saved_objects/map"

        payload = {
            "attributes": {
                "title": self.INDEX_NAME, 
                "description": "Map created using Python automation",
                "mapStateJSON": json.dumps({
                    "zoom": 2,  
                    "center": {"lon": 0, "lat": 0}, 
                    "timeFilters": {"from": "now-1h", "to": "now"},  
                    "query": {"query": "", "language": "kuery"},  
                    "filters": []  
                }),
                "layerListJSON": json.dumps([
                    {
                        "id": "basemap_layer",
                        "type": "EMS_VECTOR_TILE",
                        "sourceDescriptor": {
                            "type":"EMS_TMS",
                            "isAutoSelect":True,
                            "lightModeDefault":"road_map_desaturated"
                        },
                        "visible": True,
                        "label":"Basemap",
                        "minZoom":0,
                        "maxZoom":24,
                        "alpha":1,
                        "includeInFitToBounds":True,
                        "locale":"autoselect",
                        "style": {
                            "type": "EMS_VECTOR_TILE",
                            "color":""
                        }
                    },
                    {
                        "id": "layer_1",  
                        "type": "MVT_VECTOR", 
                        "sourceDescriptor": {
                            "type": "ES_SEARCH",  
                            "indexPatternId": data_view_id, 
                            "geoField": geo_field, 
                            "scalingType": "limit",  
                            "sortField":"attacker",
                            "sortOrder":"desc",
                            "applyGlobalQuery": True  
                        },
                        "style": {
                            "type": "STATIC",  
                            "properties": {
                                "fillColor": {"type": "DYNAMIC", "options": {"field":{"name":"attacker","origin":"source"},"type":"CATEGORICAL","useCustomColorPalette":False,"colorCategory":"palette_0"}},  
                                "lineColor": {"type": "STATIC", "options": {"color": "#000000"}}, 
                                "iconSize": {"type": "STATIC", "options": {"size": 6}},  
                                "icon": {"type": "STATIC", "options": {"value": "marker"}},  
                                "labelText":{"type":"STATIC", "options":{"value":"{attacker}"}},
                                "labelColor":{"type":"DYNAMIC","options":{"field":{"name":"attacker","origin":"source"},"type":"CATEGORICAL","useCustomColorPalette":False,"colorCategory":"palette_0"}},
                                "labelSize":{"type":"STATIC","options":{"size":12}}
                            }
                        }
                    }
                ])
            }
        }

        if self.check_map():
            self.delete_map()
        response = requests.post(url, headers=self.HEADERS, json=payload)

        if response.status_code == 200:
            print("Map created successfully")
            map_id = response.json()["id"]
            return map_id, 'map'
        else:
            print(f"Failed to create map: {response.status_code}, {response.text}")
            return None, None

    def create_dashboard(self):
        url = f"{self.KIBANA_URL}/api/saved_objects/dashboard/"
        payload = {
            "attributes": {
                "title": self.INDEX_NAME,
                "description": "Auto-generated dashboard",
            }
        }
        if self.check_dashboard():
            self.delete_dashboard()
        response = requests.post(url, headers=self.HEADERS, json=payload)
        if response.status_code == 200:
            dashboard_id = response.json().get("id")
            print(f"Dashboard '{self.INDEX_NAME}' created with ID: {dashboard_id}")
            return dashboard_id
        else:
            print(f"Failed to create dashboard: {response.status_code}, {response.text}")
            return None

    def get_dashboard_id(self):
        url = f"{self.KIBANA_URL}/api/saved_objects/_find?type=dashboard&search_fields=title&search={self.INDEX_NAME}"
        response = requests.get(url, headers=self.HEADERS)
        if response.status_code == 200:
            results = response.json().get("saved_objects", [])
            if results:
                dashboard_id = results[0].get("id")
                print(f"Dashboard '{self.INDEX_NAME}' found with ID: {dashboard_id}")
                return dashboard_id
            else:
                print(f"Dashboard '{self.INDEX_NAME}' not found.")
                return None
        else:
            print(f"Failed to search for dashboard: {response.status_code}, {response.text}")
            return None
    
    def add_visualization_to_dashboard(self,dashboard_id, id):
        panel_index=str(self.panel_idx)
        url = f"{self.KIBANA_URL}/api/saved_objects/dashboard/{dashboard_id}"

        response = requests.get(url, headers=self.HEADERS)
        if response.status_code != 200:
            print(f"Failed to fetch dashboard: {response.status_code}, {response.text}")
            return

        dashboard = response.json()
        existing_panels = json.loads(dashboard["attributes"].get("panelsJSON", "[]"))
        new_panel = {
            "panelIndex": panel_index,
            "gridData": {
                "x": 24, 
                "y": len(existing_panels) * 15, 
                "w": 24,  
                "h": 15,  
                "i": panel_index 
            },
            "version": "8.15.1", 
            "type": "visualization",
            "id": id  
        }


        existing_panels.append(new_panel)
        updated_dashboard = {
            "attributes": {
                **dashboard["attributes"],
                "panelsJSON": json.dumps(existing_panels),
                "timeRestore": False,
                "kibanaSavedObjectMeta":
                    {
                        "searchSourceJSON": json.dumps(
                            {"query": {"query": "", "language": "lucene"}, "filter": [], "highlightAll": True,
                             "version": True})
                    },
                "optionsJSON": json.dumps({"darkTheme": False, "useMargins": True, "hidePanelTitles": False}),
            },
        }
        data = json.dumps(updated_dashboard)
        response = requests.post(url+"?overwrite=true", headers=self.HEADERS, data=data)
        if response.status_code == 200:
            print(f"Visualization '{id}' added to Dashboard '{dashboard_id}'.")
        else:
            print(f"Failed to update dashboard: {response.status_code}, {response.text}")

        self.panel_idx+=1

    def add_map_to_dashboard(self,dashboard_id, id):
        panel_index=str(self.panel_idx)
        url = f"{self.KIBANA_URL}/api/saved_objects/dashboard/{dashboard_id}"

        response = requests.get(url, headers=self.HEADERS)
        if response.status_code != 200:
            print(f"Failed to fetch dashboard: {response.status_code}, {response.text}")
            return

        dashboard = response.json()
        existing_panels = json.loads(dashboard["attributes"].get("panelsJSON", "[]"))
        new_panel = {
            "panelIndex": panel_index,
            "gridData": {
                "x": 0, 
                "y": len(existing_panels) * 15,  
                "w": 24,  
                "h": 15,  
                "i": panel_index 
            },
            "version": "8.15.1", 
            "type": "map",
            "id": id  
        }

        existing_panels.append(new_panel)
        updated_dashboard = {
            "attributes": {
                **dashboard["attributes"],
                "panelsJSON": json.dumps(existing_panels),
                "timeRestore": False,
                "kibanaSavedObjectMeta":
                    {
                        "searchSourceJSON": json.dumps(
                            {"query": {"query": "", "language": "lucene"}, "filter": [], "highlightAll": True,
                             "version": True})
                    },
                "optionsJSON": json.dumps({"darkTheme": False, "useMargins": True, "hidePanelTitles": False}),
            },
        }
        data = json.dumps(updated_dashboard)
        response = requests.post(url+"?overwrite=true", headers=self.HEADERS, data=data)
        if response.status_code == 200:
            print(f"Visualization '{id}' added to Dashboard '{dashboard_id}'.")
        else:
            print(f"Failed to update dashboard: {response.status_code}, {response.text}")

        self.panel_idx+=1

    def check_index_pattern(self):
        response = self.es.indices.exists(index=self.INDEX_NAME)
        return response

    def delete_index_pattern(self):
        response = self.es.indices.delete(index=self.INDEX_NAME)
        print(response)

    def check_data_view(self):
        search_url = f"{self.KIBANA_URL}/api/saved_objects/_find?type=index-pattern&search_fields=title&search={self.INDEX_NAME}" 
        response = requests.get(search_url, headers=self.HEADERS) 
        return response.json()['total']>0

    def delete_data_view(self): 
        search_url = f"{self.KIBANA_URL}/api/saved_objects/_find?type=index-pattern&search_fields=title&search={self.INDEX_NAME}" 
        response = requests.get(search_url, headers=self.HEADERS) 
        if response.status_code == 200: 
            result = response.json() 
            if result['total'] > 0: 
                data_view_id = result['saved_objects'][0]['id'] 
                delete_url = f"{self.KIBANA_URL}/api/saved_objects/index-pattern/{data_view_id}" 
                delete_response = requests.delete(delete_url, headers=self.HEADERS) 
                if delete_response.status_code == 200: 
                    print(f"Data view '{self.INDEX_NAME}' has been successfully deleted.") 
                else: 
                    print(f"Failed to delete data view '{self.INDEX_NAME}': {delete_response.status_code}, {delete_response.text}") 
            else: 
                print(f"Data view '{self.INDEX_NAME}' not found.") 
        else: 
            print(f"Failed to search for data view '{self.INDEX_NAME}': {response.status_code}, {response.text}")

    def check_map(self):
        url = f"{self.KIBANA_URL}/api/saved_objects/_find?type=map&search_fields=title&search={self.INDEX_NAME}"
        response = requests.get(url, headers=self.HEADERS)
        return response.json()['total']>0

    def delete_map(self):
        url = f"{self.KIBANA_URL}/api/saved_objects/_find?type=map&search_fields=title&search={self.INDEX_NAME}"
        response = requests.get(url, headers=self.HEADERS)
        if response.status_code == 200:
            visualizations = response.json().get("saved_objects", [])
            for viz in visualizations:
                if viz["attributes"]["title"] == self.INDEX_NAME:
                    viz_id = viz["id"]
                    delete_url = f"{self.KIBANA_URL}/api/saved_objects/map/{viz_id}"
                    delete_response = requests.delete(delete_url, headers=self.HEADERS)
                    if delete_response.status_code == 200:
                        print(f"map '{self.INDEX_NAME}' deleted successfully.")
                    else:
                        print(f"Failed to delete map '{self.INDEX_NAME}': {delete_response.status_code}, {delete_response.text}")
        else:
            print(f"Failed to fetch Visualizations: {response.status_code}, {response.text}")

    def check_visualization(self):
        url = f"{self.KIBANA_URL}/api/saved_objects/_find?type=visualization&search_fields=title&search={self.INDEX_NAME}"
        response = requests.get(url, headers=self.HEADERS)
        return response.json()['total']>0

    def delete_visualization(self):
        url = f"{self.KIBANA_URL}/api/saved_objects/_find?type=visualization&search_fields=title&search={self.INDEX_NAME}"
        response = requests.get(url, headers=self.HEADERS)
        if response.status_code == 200:
            visualizations = response.json().get("saved_objects", [])
            for viz in visualizations:
                if viz["attributes"]["title"] == self.INDEX_NAME:
                    viz_id = viz["id"]
                    delete_url = f"{self.KIBANA_URL}/api/saved_objects/visualization/{viz_id}"
                    delete_response = requests.delete(delete_url, headers=self.HEADERS)
                    if delete_response.status_code == 200:
                        print(f"Visualization '{self.INDEX_NAME}' deleted successfully.")
                    else:
                        print(f"Failed to delete Visualization '{self.INDEX_NAME}': {delete_response.status_code}, {delete_response.text}")
        else:
            print(f"Failed to fetch Visualizations: {response.status_code}, {response.text}")

    def check_dashboard(self):
        url = f"{self.KIBANA_URL}/api/saved_objects/_find?type=dashboard&search_fields=title&search={self.INDEX_NAME}"
        response = requests.get(url, headers=self.HEADERS)
        return response.json()['total']>0

    def delete_dashboard(self):
        url = f"{self.KIBANA_URL}/api/saved_objects/_find?type=dashboard&search_fields=title&search={self.INDEX_NAME}"
        response = requests.get(url, headers=self.HEADERS)
        if response.status_code == 200:
            dashboards = response.json().get("saved_objects", [])
            for dashboard in dashboards:
                if dashboard["attributes"]["title"] == self.INDEX_NAME:
                    dashboard_id = dashboard["id"]
                    delete_url = f"{self.KIBANA_URL}/api/saved_objects/dashboard/{dashboard_id}"
                    delete_response = requests.delete(delete_url, headers=self.HEADERS)
                    if delete_response.status_code == 200:
                        print(f"Dashboard '{self.INDEX_NAME}' deleted successfully.")
                    else:
                        print(f"Failed to delete Dashboard '{self.INDEX_NAME}': {delete_response.status_code}, {delete_response.text}")
        else:
            print(f"Failed to fetch Dashboards: {response.status_code}, {response.text}")

    def process(self):
        self.init_elk()
        self.delete_all_documents()
        self.create_mapping()
        self.upload_data_view()
        self.create_data_view()
        vis_id = self.create_table_visualization(self.get_index_pattern_id())
        map_id = self.create_map_with_es_layer(self.get_index_pattern_id())

        board_id = self.get_dashboard_id()
        self.create_dashboard()
        board_id = self.get_dashboard_id()

        ids = [vis_id,map_id]
        for id, type in ids:
            if type=='visualization':
                self.add_visualization_to_dashboard(board_id,id)
            elif type=='map':
                self.add_map_to_dashboard(board_id,id)
#