import json
import random
from itertools import chain
from typing import List, Tuple
from datetime import datetime

import requests

from data import HouseEntry


BASE = 'https://asunnot.oikotie.fi'


class OTClient:
    """OTClient

    Oikotie Client to fetch house data with.

    Examples
    --------
    >>> with OTClient() as c:
    >>>     for entry in c.query(['Keskusta, Helsinki']):
    >>>         # Do something with the data
    """
    def __enter__(self):
        self.session = requests.Session()
        self.headers = self.ota
        return self

    def __exit__(self, *args):
        self.session.close()

    def query(self, locations: List[str]=None, house_type: List[str]=None, 
              room_count: List[int]=None, price_min: int=None, price_max: int=None,
              size_min: int=None, size_max: int=None, limit: int=50):
        """House query

        Returns an iterator of the results.

        Parameters
        ----------
        locations : list of str
            Street or area names as locations
        house_type : list of str
            House type selections
        room_count : list of int
            Number of rooms
        price_min : int
            Minimum price for house
        price_max : int
            Maximum price for house
        size_min : int
            Minimum size in cubic meters
        size_max : int
            Maximum size in cubic meters
        limit : int, default=50
            Limit of results for each request
        """
        params = {k: v for k, v in locals().items() if k != 'self'}
        params.update({
            'limit': limit,
            'cardType': 101,
            'offset': 0,
            'sortBy': 'published_sort_desc'
        })

        def _execute():
            url = BASE + '/api/cards' + self._params_builder(**params)
            res = self.session.get(url, headers=self.headers)
            return res.json()

        data = _execute()
        for entry in data['cards']:
            yield self._entry_builder(entry)

        n_found = data['found']

        if n_found > limit:
            for i in range(limit, n_found, limit):
                params['offset'] = i
                data = _execute()
                for entry in data['cards']:
                    yield self._entry_builder(entry)

    def location(self, *locations: Tuple[str]):
        """Locations

        Fetches the internal location ids by name.

        Parameters
        ----------
        locations : tuple of str
            Street or area names as locations

        Returns
        -------
        results : str
            Encoded string of the results
        """
        results = '['
        keys = ['cardId', 'cardType']

        for loc in locations:
            url = BASE + '/api/3.0/location'
            params = params={'query': loc}
            res = self.session.get(url, params=params, headers=self.headers)

            for entry in res.json():
                data = entry['card']
                info = str([data[k] for k in keys]).replace(' ', '')[:-1]
                info += f',\"{loc.replace(" ", "+")}\"]'
                results += f'{info},'

        results = results[:-1]
        results += ']'

        return results

    @property
    def headers(self):
        return self.__headers

    @headers.setter
    def headers(self, data: dict):
        if 'User-Agent' not in data:
            data['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0'
        self.__headers = data

    @property
    def ota(self):
        """OTA info

        Fetches the user token and id dynamically for headers

        Returns
        -------
        ota : dict
            OTA data
        """
        num = random.randint(0, int(9e3))
        url = BASE + f'/user/get?format=json&rand={num}'
        res = self.session.get(url)
        data = res.json()['user']
        ota = {
            'OTA-cuid': data['cuid'],
            'OTA-loaded': str(data['time']),
            'OTA-token': data['token']
        }
        return ota

    def _params_builder(self, **params) -> str:
        """Builds API request parameters from dictionary"""
        param_map = dict(
            house_type='buildingType[]',
            room_count='roomCount[]',
            price_min='price[min]',
            price_max='price[max]',
            size_min='size[min]',
            size_max='size[max]'
        )
        house_types = dict(
            kerrostalo=[1, 256],
            rivitalo=[2],
            paritalo=[64],
            omakotitalo=[4, 8, 32, 128],
        )
        params['house_type'] = list(chain(*[house_types[k] for k in params['house_type']]))
        params['locations'] = self.location(*params['locations'])

        parameters = '?'
        for key, value in params.items():
            if not value:
                continue
            if key in param_map:
                key = param_map[key]
            if isinstance(value, list,):
                for v in value:
                    parameters += f'{key}={v}&'
            else:
                parameters += f'{key}={value}&'
        return parameters[:-1]

    def _entry_builder(self, entry) -> HouseEntry:
        """Converts the JSON as internal HouseEntry data"""
        data = {k: v for k, v in entry.items() if k in HouseEntry.__dataclass_fields__}
        data.update(entry.get('buildingData', {}))

        data['description'] = data.pop('description', '').replace('\n', '')
        data['building_type'] = data.pop('buildingType', None)
        data['room_configuration'] = entry.get('roomConfiguration', None)
        data['brand_name'] = entry.get('brand', {'name': None})['name']

        coordinates = entry.get('coordinates', {})
        data['longitude'] = coordinates.get('longitude', None)
        data['latitude'] = coordinates.get('latitude', None)

        data['price_changed'] = self._convert_ts(entry.get('priceChanged', None))
        data['published'] = self._convert_ts(entry.get('published', None))

        return HouseEntry(**data)

    def _convert_ts(self, ts: str):
        """Timeformat converter"""
        return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ') if ts else None
