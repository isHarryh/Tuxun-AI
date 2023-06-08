# -*- coding: utf-8 -*-
# Copyright (c) 2023, Harry Huang
# @ BSD 3-Clause License
import json, base64, time
import requests as R
from PIL import Image
from io import BytesIO


class TuxunGame():
    '''Tuxun Game'''

    def __init__(self, resp_data:dict):
        '''Initialize a TuxunGame instance using the response data from server.'''
        self.id:str      = resp_data['id']
        '''The UUID of the game'''
        self.type:str    = resp_data['type']
        '''The game type'''
        self.teams:list  = resp_data['teams']
        '''The teams list'''
        self.status:str  = resp_data['status']
        '''The status of the game'''
        self.rounds:list = resp_data['rounds']
        '''The rounds list'''
        self.pano:str      = resp_data['rounds'][-1]['panoId'] if len(self.rounds) else None
        '''The street view pano ID'''
        self.pano_type:str = resp_data['rounds'][-1]['source'] if len(self.rounds) else None
        '''The street view pano type'''
        self.__has_answer = False
        try:
            if resp_data['player']['lastRoundResult'] and resp_data['rounds'][-1]['lng'] and resp_data['rounds'][-1]['lng']:
                self.__has_answer = True
                self.last_guess_dictance = resp_data['player']['lastRoundResult']['distance']
                self.last_guess_place    = resp_data['player']['lastRoundResult']['guessPlace']
                self.last_guess_target   = resp_data['player']['lastRoundResult']['targetPlace']
                self.last_guess_target_lng = resp_data['rounds'][-1]['lng']
                self.last_guess_target_lat = resp_data['rounds'][-1]['lat']
        except:
            pass
    
    def has_answer(self):
        ''':returns: Whether this game has been completed and has the answer given by server.'''
        return self.__has_answer

class TuxunAgentException(Exception):

    def __init__(self, msg:str):
        self.msg = msg
    
    def __str__(self):
        return self.msg

class TuxunAgent():
    '''Tuxun Agent'''

    def __init__(self):
        '''Initialize a TuxunGame instance.'''
        self.cookie = ""
        pass

    def set_cookie(self, cookie:str):
        '''Set the Cookie to be used to interact with the server.'''
        self.cookie = cookie
    
    def get_user_id(self):
        ''''Get the user ID of the current user.'''
        try:
            r = R.get(f"https://tuxun.fun/api/get_profile",
                headers=self.__get_http_header())

            if r.status_code == 200:
                r.encoding = 'UTF-8'
                resp = json.loads(r.text)
                if resp['success']:
                    if not resp['data']:
                        raise TuxunAgentException(f"No user ID returned.")
                    return str(resp['data']['userId'])
                else:
                    msg = resp['errorCode'] if 'errorCode' in resp.keys() else 'unknown'
                    raise TuxunAgentException(f"API operation failed, reason: {msg}")
            else:
                raise TuxunAgentException(f"HTTP request failed, response code: {r.status_code}")
        except Exception as e:
            return e
    
    def get_user_rating(self, id:int):
        '''Get the rating of the specified user.'''
        try:
            r = R.get(f"https://tuxun.fun/api/v0/tuxun/getProfile?userId={id}",
                headers=self.__get_http_header())

            if r.status_code == 200:
                r.encoding = 'UTF-8'
                resp = json.loads(r.text)
                if resp['success']:
                    return resp['data']['rating']
                else:
                    msg = resp['errorCode'] if 'errorCode' in resp.keys() else 'unknown'
                    raise TuxunAgentException(f"API operation failed, reason: {msg}")
            else:
                raise TuxunAgentException(f"HTTP request failed, response code: {r.status_code}")
        except Exception as e:
            return e
    
    def create(self, type='country', mode='streak'):
        '''
        Create a Tuxun Game.
        :param type: 'country' or 'province'.
        :param mode: 'streak'.
        :returns: TuxunGame object if success.
        '''
        try:
            r = R.get(f"https://tuxun.fun/api/v0/tuxun/{mode}/create?type={type}",
                headers=self.__get_http_header())

            if r.status_code == 200:
                r.encoding = 'UTF-8'
                resp = json.loads(r.text)
                if resp['success']:
                    return TuxunGame(resp['data'])
                else:
                    msg = resp['errorCode'] if 'errorCode' in resp.keys() else 'unknown'
                    raise TuxunAgentException(f"API operation failed, reason: {msg}")
            else:
                raise TuxunAgentException(f"HTTP request failed, response code: {r.status_code}")
        except Exception as e:
            return e
    
    def get(self, id:str, mode='solo'):
        '''
        Get a given Tuxun Game.
        :param id: Game UUID.
        :param mode: 'solo' or 'streak'.
        :returns: TuxunGame object if success.
        '''
        try:
            r = R.get(f"https://tuxun.fun/api/v0/tuxun/{mode}/get?gameId={id}",
                headers=self.__get_http_header())

            if r.status_code == 200:
                r.encoding = 'UTF-8'
                resp = json.loads(r.text)
                if resp['success']:
                    return TuxunGame(resp['data'])
                else:
                    msg = resp['errorCode'] if 'errorCode' in resp.keys() else 'unknown'
                    raise TuxunAgentException(f"API operation failed, reason: {msg}")
            else:
                raise TuxunAgentException(f"HTTP request failed, response code: {r.status_code}")
        except Exception as e:
            return e
    
    def guess(self, game:TuxunGame, lng:float, lat:float):
        '''
        Do a guess of the game.
        :param game: TuxunGame object.
        :param lng: The lng of the place.
        :param lat: The lat of the place.
        :returns: TuxunGame object if success.
        '''
        try:
            if 'streak' in game.type:
                api = 'streak'
            elif 'solo' in game.type:
                api = 'solo'
            else:
                return TuxunAgentException(f"Unsupported game type: {game.type}")
            r = R.get(f"https://tuxun.fun/api/v0/tuxun/{api}/guess?gameId={game.id}&lng={lng}&lat={lat}",
                headers=self.__get_http_header())

            if r.status_code == 200:
                r.encoding = 'UTF-8'
                resp = json.loads(r.text)
                if resp['success']:
                    return TuxunGame(resp['data'])
                else:
                    msg = resp['errorCode'] if 'errorCode' in resp.keys() else 'unknown'
                    raise TuxunAgentException(f"API operation failed, reason: {msg}")
            else:
                raise TuxunAgentException(f"HTTP request failed, response code: {r.status_code}")
        except Exception as e:
            return e

    def emoji(self, game:TuxunGame, emoji_id:int):
        '''
        Send an emoji to the given game.
        1=无语,2=困乏,3=喷水,4=恼火,5=滑稽,6=委屈,7=点赞,8=疑问,9=鄙视,10=呕吐,11=欢呼,12=悲伤,13=得意,14=吃瓜
        :param game: TuxunGame object.
        :param emoji_id: Emoji ID.
        :returns: True if success.
        '''
        try:
            if 'solo' in game.type:
                api = 'solo'
            else:
                return TuxunAgentException(f"Unsupported game type: {game.type}")
            r = R.get(f"https://tuxun.fun/api/v0/tuxun/{api}/sendEmoji?gameId={game.id}&emojiId={emoji_id}",
                headers=self.__get_http_header())

            if r.status_code == 200:
                r.encoding = 'UTF-8'
                resp = json.loads(r.text)
                if resp['success']:
                    return True
                else:
                    msg = resp['errorCode'] if 'errorCode' in resp.keys() else 'unknown'
                    raise TuxunAgentException(f"API operation failed, reason: {msg}")
            else:
                raise TuxunAgentException(f"HTTP request failed, response code: {r.status_code}")
        except Exception as e:
            return e

    def match(self, mode='solo'):
        '''
        Match a PVP game.
        :param mode: 'solo'.
        :returns: Game ID string if success.
        '''
        try:
            interval = 1500
            match = None
            while not match:
                r = R.get(f"https://tuxun.fun/api/v0/tuxun/{mode}/joinRandom?interval={interval}",
                    headers=self.__get_http_header())

                if r.status_code == 200:
                    r.encoding = 'UTF-8'
                    resp = json.loads(r.text)
                    if resp['data']:
                        match = resp['data']
                else:
                    raise TuxunAgentException(f"HTTP request failed, response code: {r.status_code})")
                time.sleep(interval / 1000)

            return match
        except Exception as e:
            return e
    
    def join(self, id:str):
        '''
        Join-in a multi-player game.
        :param id: Game ID string.
        :returns: TuxunGame object if success.
        '''
        try:
            r = R.get(f"https://tuxun.fun/api/v0/tuxun/game/join?gameId={id}",
                headers=self.__get_http_header())

            if r.status_code == 200:
                r.encoding = 'UTF-8'
                resp = json.loads(r.text)
                if resp['success']:
                    return TuxunGame(resp['data'])
                else:
                    msg = resp['errorCode'] if 'errorCode' in resp.keys() else 'unknown'
                    raise TuxunAgentException(f"API operation failed, reason: {msg}")
            else:
                raise TuxunAgentException(f"HTTP request failed, response code: {r.status_code}")
        except Exception as e:
            return e

    def __get_http_header(self):
        return {
            'cookie': self.cookie
        }

class StreetViewException(Exception):

    def __init__(self, msg:str):
        self.msg = msg
    
    def __str__(self):
        return self.msg

class StreetView():
    '''Street View'''

    T_AUTO_DETECT   = 0
    T_BAIDU_PANO    = 1
    T_GOOGLE_PANO   = 2
    T_CHAOFAN_PANO  = 3

    def __init__(self, pano:str, type:int=T_AUTO_DETECT):
        self.pano = pano
        '''The pano ID of the street view.'''
        self.__type = type

    def get_type(self):
        if self.__type == self.T_BAIDU_PANO:
            return self.T_BAIDU_PANO
        if self.__type == self.T_GOOGLE_PANO:
            return self.T_GOOGLE_PANO
        if self.__type == self.T_CHAOFAN_PANO:
            return self.T_CHAOFAN_PANO
        if len(self.pano) == 22:
            return self.T_GOOGLE_PANO
        if len(self.pano) == 64:
            return self.T_CHAOFAN_PANO
        return StreetViewException(f"Unable to detect the type of the pano ID: {self.pano}")

    def get_image(self, x:int=0, y:int=0, z:int=0):
        img = self.get_image_bytes(x, y, z)
        if type(img) == bytes:
            return Image.open(BytesIO(img))
        return img

    def get_image_bytes(self, x:int=0, y:int=0, z:int=0):
        t = self.get_type()
        if t == self.T_BAIDU_PANO:
            return None
        if t == self.T_GOOGLE_PANO:
            return self.__get_google_street_view(self.pano, x, y, z)
        if t == self.T_CHAOFAN_PANO:
            return self.__get_chaofan_street_view(self.pano, x, y, z)

    @staticmethod
    def __get_google_street_view(pano_id:str, x:int=0, y:int=0, zoom:int=0):
        try:
            r = R.get(f"https://streetviewpixels-pa.googleapis.com/cbk?cb_client=apiv3&panoid={pano_id}&output=tile&x={x}&y={y}&zoom={zoom}&nbt=1&fover=2",
                    timeout=10)
            
            if r.status_code == 200:
                return r.content
            else:
                raise StreetViewException(f"HTTP request failed, response code: {r.status_code}")
        except Exception as e:
            return e

    @staticmethod
    def __get_chaofan_street_view(pano_id:str, x:int=0, y:int=0, z:int=0):
        encoding = 'UTF-8'
        try:
            pano_id = str(base64.decodebytes(bytes(pano_id, encoding=encoding)), encoding=encoding)
            pano_id = pano_id[pano_id.find(',')+1:]
            r = R.get(f"https://map.chao-fan.com/p/{pano_id}=x{x}-y{y}-z{z}",
                    timeout=10)
            
            if r.status_code == 200:
                return r.content
            else:
                raise StreetViewException(f"HTTP request failed, response code: {r.status_code}")
        except Exception as e:
            return e
