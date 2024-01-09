from PIL import Image
from telegraph import Telegraph
from html_telegraph_poster import upload_image

import pyshorteners, os
from django.conf import settings 

class TelegraphGenerator:

    def __init__(self, access_token: str) -> None:
        self.telegraph_generator = Telegraph(access_token=access_token)
        self.type_tiny = pyshorteners.Shortener() 

    def _generate_html(self, preview_path: str, content_dir: str, user_channel_link:str, username:str) -> None:
        
        """данная функция реализует генерацию телеграф-поста используя html-шаблон

        Args:
            preview_path (str): путь до заглавной фотки, которая будет видна в превью
            content_dir (str): путь до остальных фоток
            user_channel_link (str): ссылка на канал заказчика
            username (str): юзернейм админа этого канала

        Returns:
            _type_: ссылка на телеграф-пост
        """

        user_channel_link = self.type_tiny.tinyurl.short(user_channel_link)
        html_header = f'<p dir="auto">Оформление верхнего блока</p>'\
                      f'<hr></hr>'
    
        html_first_pht = f"<img src='{upload_image(preview_path)}'/><br>"
        
        html_middle = f'''<a href="{user_channel_link}" target="_blank">⚡️ПОЛУЧИТЬ ДОСТУП К VIP⚡️ </a>
                    <p dir="auto"><br></p>
                    <h4 dir="auto" id="Личные-данные⭐️">Личные данные⭐️</h4>
                    <ul dir="auto">
                        <li>
                            <strong><em>Имя: </em></strong>
                            <p>
                                <em>Вика</em> 
                            </p>
                        </li>
                        <li>
                            <strong><em>Фамилия: </em></strong>
                            <p>
                                <em>Кир</em>----- 
                            </p>
                        </li>
                        <li>
                            <strong><em>Город: </em></strong>
                            <p>
                                <em>Екатеринбург</em> 
                            </p>
                        </li>
                        <li>
                            <strong><em>Возраст: </em></strong>
                            <p>
                                <em>20</em> 
                            </p>
                        </li>
                    </ul>
                    <p dir="auto"><br></p>
                    <h4 dir="auto" id="Интим-фото💫">Интим фото💫</h4>
                    '''
        
        html_outer = f'''
                        <h4 dir="auto" id="О-нашем-привате🔥">О нашем привате🔥</h4>
                        <p dir="auto"><br></p>
                        <p dir="auto">В каналах на данный момент находится более <em>1000</em> архивов! Каналы регулярно пополняется! </p>
                        <p dir="auto">В наши каналы мы выгружаем фото, видео, переписки (<em>в формате html</em>), это делает наши приваты более уникальными! </p>
                        <p dir="auto">Поверьте здесь есть на что посмотреть, контент уникальный и не повторяется ни с одним из каналов! </p>
                        <p dir="auto"><br></p>
                        <h4 dir="auto" id="Как-получить-приват?✨">Как получить приват?✨</h4>
                        <ul dir="auto">
                            <li>Через Privat Бот - 
                                <a href="{user_channel_link}" target="_blank">Канал</a>
                            </li>
                            <li>Лично через админа: 
                                <a href="{user_channel_link}" target="_blank">@{username}</a>
                            </li>
                        </ul>
                    '''
            
        html_photos = ''
        
        for photo in os.listdir(content_dir):
            if photo.split(".")[-1].strip().lower() not in ("jpg", "jpeg", "png"):
                continue 
            
            html_photos += f"<img src='{upload_image(content_dir + photo)}'/><br>"
            
        html = html_header + html_first_pht + html_middle + html_photos + html_outer
        response = self.telegraph_generator.create_page(title='Архив', html_content=html,
                                        author_name=f'Product by {username}', 
                                        author_url=user_channel_link)

        return ('https://telegra.ph/{}'.format(response['path']))
