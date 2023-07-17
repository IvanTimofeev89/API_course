import requests
import datetime
import time
import json
from progress.bar import IncrementalBar
from urllib.parse import urlencode


class VKClient:
    vk_url = 'https://api.vk.com/method/photos.get'
    y_disk_url = 'https://cloud-api.yandex.net/v1/disk/resources'
    folder_name = 'vk_backup'
    photo_amount = 5

    def __init__(self, vk_token, user_id, disk_token, album_id):
        self.vk_token = vk_token
        self.user_id = user_id
        self.album_id = album_id
        self.vk_params = {
            'access_token': self.vk_token,
            'v': '5.131',
            'owner_id': self.user_id,
            'album_id': self.album_id,
            'extended': 1
        }
        self.disk_token = disk_token
        self.y_headers = {'Authorization': f'OAuth {self.disk_token}'}

    def _get_vk_photos(self):
        response = requests.get(self.vk_url, params=self.vk_params)
        response.raise_for_status()
        return response.json().get('response').get('items')

    def _create_disk_folder(self):
        res = requests.put(self.y_disk_url, params={'path': self.folder_name}, headers=self.y_headers)
        res.raise_for_status()
        return res.status_code

    def _post_and_json(self, _list, _path, _date, _url, _json, _size):
        """Функция:
         1) выбирает имя файла ("лайки" или "лайки+дата") основываясь на списке likes_list
         2) отправляет фото на Яндекс.Диск
         3) формирует список json_data для дальнейшего создания json файла
        Списки likes_list и json_data создаются в основной функции y_disk_upload
        """
        likes_number = _path
        params = {'url': _url}
        if _list.count(likes_number) > 1:
            date = datetime.datetime.fromtimestamp(_date).strftime('%d%m%Y')
            file_name = f'{likes_number}' + f' {date}'
            params.update({'path': f'/{self.folder_name}/' + file_name})
            res = requests.post(self.y_disk_url + '/upload', params=params, headers=self.y_headers)
            res.raise_for_status()
            _json.append({'file_name': f'{file_name}.jpg', 'size': _size})
        else:
            file_name = f'{likes_number}'
            params.update({'path': f'/{self.folder_name}/' + file_name})
            res = requests.post(self.y_disk_url + '/upload', params=params, headers=self.y_headers)
            res.raise_for_status()
            _json.append({'file_name': f'{file_name}.jpg', 'size': _size})

    def _make_json(self, data, name):
        with open(name, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def y_disk_upload(self):
        """Основная вызываемая функция. Включает в себя:
        1) создание папки на Яндекс.Диск
        2) отправка фото на Яндекс.Диск
        3) отображение прогресс-бара в терминале
        4) создание выходного json файла"""
        if self._create_disk_folder() == 201:
            photos_list = self._get_vk_photos()[:self.photo_amount]
            likes_list = [i.get('likes').get('count') for i in photos_list]
            json_data = []
            bar = IncrementalBar('Countdown', max=len(photos_list))
            for item in photos_list:
                for picture in item['sizes']:
                    if picture['type'] == 'z':
                        self._post_and_json(
                            _list=likes_list,
                            _path=item.get('likes').get('count'),
                            _date=item.get('date'),
                            _url=picture['url'],
                            _json=json_data,
                            _size=picture['type']
                        )
                        bar.next()
                        time.sleep(0.5)
            bar.finish()
            self._make_json(data=json_data, name='vk_backup.json')


def get_access_token():
    vk_app_id = 51699734
    oauth_base_url = "https://oauth.vk.com/authorize"
    params = {
        "client_id": vk_app_id,
        "redirect_uri": "https://oauth.vk.com/blank.html",
        "display": "page",
        "scope": "photos",
        "response_type": "token"
    }
    return f'{oauth_base_url}?{urlencode(params)}'


if __name__ == "__main__":
    album_types = {'1': 'profile', '2': 'saved', '3': 'wall'}
    print(f'Перейдите по следующей ссылке и скопируйте '
          f'acess_token\n{get_access_token()}')
    vk_token = input('Введите VK access token: ').strip()
    disk_token = input('Введите Яндекс.Диск токен: ').strip()
    vk_user_id = input('Введите VK ID пользователя: ').strip()
    album_id = input('Введите порядковый номер сохраняемого альбома '
                     '(1 - профиль, 2 - сохранные, 3 - стена): ').strip()
    vk_client = VKClient(vk_token, vk_user_id, disk_token, album_types[album_id])
    vk_client.y_disk_upload()
