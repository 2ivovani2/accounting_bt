from PIL import Image
from telegraph import Telegraph
from html_telegraph_poster import upload_image

import pyshorteners, os, random
import pandas as pd
from django.conf import settings 

class TelegraphGenerator:

    def __init__(self, access_token: str) -> None:
        self.telegraph_generator = Telegraph(access_token=access_token)
        self.type_tiny = pyshorteners.Shortener() 

    def _generate_city(self) -> str:
        cities_row = pd.read_csv('tf_maker/datasets/city.csv')[['city', 'city_type', 'population']]
        
        cities_row = cities_row.loc[(cities_row['city_type'] == 'г') & (cities_row['population'] > 300000)]
        cities_row = cities_row.sort_values(by='population', ascending=False).reset_index(drop=True)
        
        cities_array = list(cities_row.city.values)
        random_city = cities_array[random.randint(0, len(cities_array))]

        russian_letters = ['ц', 'у', 'к', 'е', 'н', 'г', 'з', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'с', 'и', 'б', 'м']
        random_address = random_city + ', ул. ' + random.choice(russian_letters).upper() + '*' * random.randint(4, 7)

        return random_address

    def _generate_age(self) -> int:
        random_year = random.randint(18, 24)
        return random_year

    def _generate_name(self) -> str:
        names = open('tf_maker/datasets/female_names_rus.txt', 'r')
        names_buff = names.read().split('\n')
        names_buff.remove('')

        random_name = random.choice(names_buff)
        return random_name

    def _generate_surname(self) -> str:
        surnames = open('tf_maker/datasets/male_surnames_rus.txt', 'r')
        surnames_buff = surnames.read().split('\n')
        surnames_buff.remove('')

        random_surname = random.choice(surnames_buff)
        return random_surname[:3] + ("*" * random.randint(3, 6))

    def _generate_phone_number(self) -> str:
        nums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        random_phone = '+7'
        
        for i in range(10):
            if i == 6 or i == 7:
                random_phone += '*'
                continue

            random_phone += random.choice(nums)
        
        return random_phone

    def _generate_vk_id(self) -> str:
        nums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        random_vk_id = 'https://vk.com/id'
        
        for i in range(random.randint(8, 11)):
            if i == 6 or i == 7:
                random_vk_id += '*'
                continue
            
            random_vk_id += random.choice(nums)
                
        return random_vk_id

    def _generate_html(self, preview_path: str, content_dir: str, user_channel_link:str, username:str) -> str:
        
        """данная функция реализует генерацию телеграф-поста используя html-шаблон

        Args:
            preview_path (str): путь до заглавной фотки, которая будет видна в превью
            content_dir (str): путь до остальных фоток
            user_channel_link (str): ссылка на канал заказчика
            username (str): юзернейм админа этого канала

        Returns:
            str: ссылка на телеграф-пост
        """

        user_channel_link = self.type_tiny.tinyurl.short(user_channel_link)
        
        html_header = f''''''
        html_first_pht = f"<img src='{upload_image(preview_path)}'/><br>"
        
        html_middle = f"""
                    <blockquote dir="auto">| {self._generate_name()}, {self._generate_age()}</blockquote>
                    <blockquote dir="auto">
                        <a href="{user_channel_link}" target="_blank">| Город: {self._generate_city()}</a>
                    </blockquote>
                    <blockquote dir="auto">
                        <a href="{user_channel_link}" target="_blank">| Телефон: {self._generate_phone_number()}</a>
                    </blockquote>
                    <blockquote dir="auto">
                        <a href="{user_channel_link}" target="_blank">| Соц.сеть: {self._generate_vk_id()}</a>
                    </blockquote>
                <img src='{self.type_tiny.tinyurl.short("https://telegra.ph/file/f4ae5521cb4f1f5b7d777.jpg")}'>    
            """

        html_photos = f''''''
        
        html_outer = f'''
                    <img src='{self.type_tiny.tinyurl.short("https://telegra.ph/file/16acc2b6aec250e7a71f6.jpg")}'>
                    <p dir="auto"><strong>+ ВСЕ ФУЛЛЫ С НЕЙ УЖЕ ДОСТУПНЫ В </strong>
                        <a href="{user_channel_link}" target="_blank">
                            <strong>ПРИВАТЕ</strong>
                        </a>
                        <a href="{self.type_tiny.tinyurl.short('https://t.me/Iskyshenie_vip_bot')}" target="_blank" data-title="{self.type_tiny.tinyurl.short('https://t.me/Iskyshenie_vip_bot')}">
                            <strong> 👑</strong>
                        </a>
                    </p>
                    '''
        
        for photo in os.listdir(content_dir):
            if photo.split(".")[-1].strip().lower() not in ("jpg", "jpeg", "png"):
                continue 
            
            html_photos += f"<img src='{upload_image(content_dir + photo)}'/><br>"
            
        html = html_header + html_first_pht + html_middle + html_photos + html_outer
        response = self.telegraph_generator.create_page(title='Архив', html_content=html,
                                        author_name=f'Product by {username}', 
                                        author_url=user_channel_link)

        return f"https://telegra.ph/{response['path']}"
