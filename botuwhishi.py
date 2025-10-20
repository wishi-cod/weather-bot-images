import os
import random
import requests
import telebot
import time
from datetime import datetime

# Конфигурация (в продакшене перенести в переменные окружения)
TOKEN = "8327112856:AAGraTlfR5_BCUbmJdHWiB_p21qGznxUebE"
WEATHERAPI_KEY = "bcf02dcbcbae43efb4b201514251410"

# Пути
GITHUB_BASE_URL = "https://raw.githubusercontent.com/kostyap1488-hue/weather-bot-images/main/"

# Инициализация бота
bot = telebot.TeleBot(TOKEN, threaded=False)
user_data = {}

class WeatherIcons:
    """Система значков и переводов погоды"""
    
    WEATHER_MAPPING = {
        'sunny': '☀️', 'clear': '☀️',
        'partly cloudy': '⛅', 'cloudy': '☁️', 'overcast': '☁️',
        'patchy rain possible': '🌦️', 'light rain': '🌦️', 'moderate rain': '🌧️',
        'heavy rain': '🌧️', 'light snow': '❄️', 'heavy snow': '❄️',
        'thundery outbreaks possible': '⛈️', 'mist': '🌫️', 'fog': '🌫️',
        'patchy light rain': '🌦️', 'moderate rain at times': '🌧️',
        'heavy rain at times': '🌧️', 'light rain shower': '🌦️',
        'moderate or heavy rain shower': '🌧️', 'light snow showers': '❄️',
        'moderate or heavy snow showers': '❄️', 'patchy light snow': '❄️',
    }
    
    TRANSLATIONS = {
        'Sunny': 'солнечно', 'Clear': 'ясно',
        'Partly cloudy': 'переменная облачность', 
        'Cloudy': 'облачно', 'Overcast': 'пасмурно',
        'Patchy rain possible': 'возможен дождь',
        'Light rain': 'небольшой дождь', 
        'Moderate rain': 'умеренный дождь',
        'Heavy rain': 'сильный дождь',
        'Light snow': 'небольшой снег',
        'Heavy snow': 'сильный снег',
        'Thundery outbreaks possible': 'возможна гроза',
        'Mist': 'дымка', 'Fog': 'туман',
        'Patchy light rain': 'местами небольшой дождь',
        'Moderate rain at times': 'временами умеренный дождь',
        'Heavy rain at times': 'временами сильный дождь',
        'Light rain shower': 'небольшой ливень',
        'Moderate or heavy rain shower': 'умеренный или сильный ливень',
        'Light snow showers': 'небольшой снегопад',
        'Moderate or heavy snow showers': 'умеренный или сильный снегопад',
        'Patchy light snow': 'местами небольшой снег',
    }
    
    @staticmethod
    def get_condition_emoji(condition, is_day=True):
        condition_lower = condition.lower()
        
        for weather_key, emoji in WeatherIcons.WEATHER_MAPPING.items():
            if weather_key in condition_lower:
                if weather_key in ['clear', 'sunny'] and not is_day:
                    return '🌙'
                return emoji
        return '🌤️'
    
    @staticmethod
    def get_condition_russian(condition):
        return WeatherIcons.TRANSLATIONS.get(condition, condition)
    
    @staticmethod
    def get_wind_strength(speed_kmh):
        if speed_kmh < 5: return "штиль"
        elif speed_kmh < 15: return "легкий"
        elif speed_kmh < 30: return "умеренный"
        elif speed_kmh < 50: return "сильный"
        else: return "очень сильный"
    
    @staticmethod
    def get_wind_direction(degree):
        directions = ['⬇️ С', '↙️ СВ', '⬅️ В', '↖️ ЮВ', '⬆️ Ю', '↗️ ЮЗ', '➡️ З', '↘️ СЗ']
        index = round(degree / 45) % 8
        return directions[index]
    
    @staticmethod
    def get_uv_level(uv_index):
        if uv_index <= 2: return "🟢 низкий", "отлично"
        elif uv_index <= 5: return "🟡 умеренный", "хорошо"
        elif uv_index <= 7: return "🟠 высокий", "осторожно"
        elif uv_index <= 10: return "🔴 очень высокий", "опасно"
        else: return "💀 экстремальный", "очень опасно"
    
    @staticmethod
    def get_precipitation_level(precip_mm):
        if precip_mm == 0: return "нет"
        elif precip_mm < 2.5: return "слабые"
        elif precip_mm < 7.5: return "умеренные"
        elif precip_mm < 15: return "сильные"
        else: return "очень сильные"

class WeatherService:
    """Сервис для работы с погодными API"""
    
    @staticmethod
    def get_city_coordinates(city_name):
        """Получение координат города"""
        try:
            url = "http://api.weatherapi.com/v1/search.json"
            params = {'key': WEATHERAPI_KEY, 'q': city_name, 'lang': 'ru'}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    city_name_lower = city_name.lower()
                    for city in data:
                        if city['name'].lower() == city_name_lower:
                            return city['name'], city['lat'], city['lon']
                    return data[0]['name'], data[0]['lat'], data[0]['lon']
        except Exception as e:
            print(f"Ошибка получения координат: {e}")
        return None
    
    @staticmethod
    def get_weather_data(lat, lon):
        """Получение данных о текущей погоде (1 день)"""
        try:
            url = "http://api.weatherapi.com/v1/forecast.json"
            params = {
                'key': WEATHERAPI_KEY,
                'q': f"{lat},{lon}",
                'days': 1,
                'lang': 'ru',
                'aqi': 'yes'
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data if 'error' not in data else None
        except Exception as e:
            print(f"Ошибка получения погоды: {e}")
        return None

    @staticmethod
    def get_weather_data_2days(lat, lon):
        """Получение данных о текущей погоде с прогнозом на 2 дня"""
        try:
            url = "http://api.weatherapi.com/v1/forecast.json"
            params = {
                'key': WEATHERAPI_KEY,
                'q': f"{lat},{lon}",
                'days': 2,
                'lang': 'ru',
                'aqi': 'yes'
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data if 'error' not in data else None
        except Exception as e:
            print(f"Ошибка получения погоды: {e}")
        return None

class SevenDayForecastService:
    """Сервис для 7-дневного прогноза погоды через Open-Meteo"""
    
    @staticmethod
    def get_7day_forecast(lat, lon):
        """Получение прогноза на 7 дней"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'daily': [
                    'weathercode', 'temperature_2m_max', 'temperature_2m_min',
                    'precipitation_probability_max', 'windspeed_10m_max',
                    'winddirection_10m_dominant', 'uv_index_clear_sky_max',
                    'sunrise', 'sunset'
                ],
                'timezone': 'auto',
                'forecast_days': 8
            }
            
            response = requests.get(url, params=params, timeout=10)
            return response.json() if response.status_code == 200 else None
                
        except Exception as e:
            print(f"Ошибка получения 7-дневного прогноза: {e}")
            return None

class WeatherFormatter:
    """Форматирование данных о погоде"""
    
    @staticmethod
    def get_time_of_day(hour):
        if 5 <= hour < 12: return "Утро"
        elif 12 <= hour < 17: return "День"
        elif 17 <= hour < 22: return "Вечер"
        else: return "Ночь"
    
    @staticmethod
    def get_current_hour_forecast(weather_data):
        """Получение данных прогноза для текущего часа"""
        location = weather_data['location']
        forecast = weather_data['forecast']['forecastday'][0]
        local_time = datetime.strptime(location['localtime'], '%Y-%m-%d %H:%M')
        
        for hour_data in forecast['hour']:
            hour_time = datetime.strptime(hour_data['time'], '%Y-%m-%d %H:%M')
            if hour_time.hour == local_time.hour:
                return hour_data
        return None
    
    @staticmethod
    def format_current_weather(weather_data):
        """Форматирование текущей погоды с использованием данных прогноза для текущего часа"""
        if not weather_data:
            return "❌ Не удалось получить данные о погоде"
        
        location = weather_data['location']
        current = weather_data['current']
        local_time = datetime.strptime(location['localtime'], '%Y-%m-%d %H:%M')
        
        # ИСПОЛЬЗУЕМ ДАННЫЕ ПРОГНОЗА ДЛЯ ТЕКУЩЕГО ЧАСА
        current_hour_forecast = WeatherFormatter.get_current_hour_forecast(weather_data)
        
        if current_hour_forecast:
            # Используем данные из прогноза для консистентности
            condition = current_hour_forecast['condition']['text']
            is_day = current_hour_forecast['is_day'] == 1
            temp = current_hour_forecast['temp_c']
            feels_like = current_hour_forecast['feelslike_c']
            wind_speed = current_hour_forecast['wind_kph']
            wind_dir = current_hour_forecast['wind_degree']
            precip_mm = current_hour_forecast.get('precip_mm', 0)
            chance_of_rain = current_hour_forecast.get('chance_of_rain', 0)
            humidity = current_hour_forecast['humidity']
            pressure_mb = current_hour_forecast['pressure_mb']
            vis_km = current_hour_forecast['vis_km']
            uv = current_hour_forecast.get('uv', 0)
        else:
            # Запасной вариант - используем текущие данные
            condition = current['condition']['text']
            is_day = current['is_day'] == 1
            temp = current['temp_c']
            feels_like = current['feelslike_c']
            wind_speed = current['wind_kph']
            wind_dir = current['wind_degree']
            precip_mm = current.get('precip_mm', 0)
            chance_of_rain = 0
            humidity = current['humidity']
            pressure_mb = current['pressure_mb']
            vis_km = current.get('vis_km', 10)
            uv = current.get('uv', 0)
        
        city = location['name']
        condition_russian = WeatherIcons.get_condition_russian(condition)
        emoji = WeatherIcons.get_condition_emoji(condition, is_day)
        
        lines = [
            f"{emoji} **В {city} {condition_russian}**",
            f"🕐 *{local_time.strftime('%H:%M')} • {WeatherFormatter.get_time_of_day(local_time.hour)}*",
            "",
            "**🌡️ ОСНОВНЫЕ ПОКАЗАТЕЛИ**",
            ""
        ]
        
        # Температура
        temp_diff = feels_like - temp
        diff_symbol = "↑" if temp_diff > 0.5 else "↓" if temp_diff < -0.5 else "•"
        diff_text = f" ({diff_symbol}{abs(temp_diff):.0f}°)" if abs(temp_diff) > 0.5 else ""
        lines.extend([
            f"**Температура:** `{temp:.0f}°C`{diff_text}",
            f"**Ощущается:** `{feels_like:.0f}°C`"
        ])
        
        # Влажность
        lines.append(f"**Влажность:** `{humidity}%`")
        
        # Осадки
        precip_level = WeatherIcons.get_precipitation_level(precip_mm)
        if chance_of_rain > 0:
            precip_text = f"🌧️ `{precip_level}` ({precip_mm}mm, {chance_of_rain}% chance)"
        else:
            precip_text = f"🌧️ `{precip_level}` ({precip_mm}mm)" if precip_mm > 0 else "☀️ `нет осадков`"
        lines.append(f"**Осадки:** {precip_text}")
        
        # Ветер
        wind_strength = WeatherIcons.get_wind_strength(wind_speed)
        wind_direction = WeatherIcons.get_wind_direction(wind_dir)
        wind_gust = current.get('gust_kph', 0)
        wind_text = f"{wind_strength} (`{wind_speed} км/ч` {wind_direction})"
        if wind_gust > wind_speed + 10:
            wind_text += f" 💨 порывы до `{wind_gust} км/ч`"
        lines.append(f"**Ветер:** {wind_text}")
        
        # Дополнительные параметры
        uv_level, uv_status = WeatherIcons.get_uv_level(uv)
        lines.extend([
            f"**УФ-индекс:** {uv_level} `{uv:.1f}` ({uv_status})",
            f"**Давление:** `{pressure_mb:.1f} гПа`",
            f"**Видимость:** `{vis_km} км`"
        ])
        
        # Рекомендации
        lines.extend(["", "**💡 РЕКОМЕНДАЦИИ**", ""])
        recommendations = WeatherFormatter._get_recommendations(
            temp, feels_like, humidity, wind_speed, uv, precip_mm, vis_km
        )
        lines.extend(recommendations)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_6hour_forecast(weather_data):
        """Форматирование прогноза на 6 часов с учетом перехода на следующий день"""
        if not weather_data:
            return "❌ Не удалось получить данные о погоде"
        
        location = weather_data['location']
        current = weather_data['current']
        forecast_days = weather_data['forecast']['forecastday']
        local_time = datetime.strptime(location['localtime'], '%Y-%m-%d %H:%M')
        
        lines = [
            f"🕒 **ТОЧНЫЙ ПРОГНОЗ НА 6 ЧАСОВ - {location['name']}**",
            f"*Начало: {local_time.strftime('%H:%M')} • {WeatherFormatter.get_time_of_day(local_time.hour)}*",
            "",
            "⏰ **ПОЧАСОВОЙ ПРОГНОЗ**",
            "",
            "┌──────────┬────────┬─────────────┬────────┬────────┐",
            "│  Время   │ Погода │ Температура │ Осадки │ Ветер  │",
            "├──────────┼────────┼─────────────┼────────┼────────┤"
        ]
        
        # Собираем часы из текущего дня
        current_day_hours = forecast_days[0]['hour'][local_time.hour:]
        hours_forecast = current_day_hours
        
        # Если нужно больше часов, добавляем из следующего дня
        if len(hours_forecast) < 6 and len(forecast_days) > 1:
            next_day_hours = forecast_days[1]['hour'][:6 - len(hours_forecast)]
            hours_forecast.extend(next_day_hours)
        
        # Ограничиваем 6 часами
        hours_forecast = hours_forecast[:6]
        
        for i, hour_data in enumerate(hours_forecast):
            hour_time = datetime.strptime(hour_data['time'], '%Y-%m-%d %H:%M')
            
            # ДЛЯ ПЕРВОГО ЧАСА ("Сейчас") ИСПОЛЬЗУЕМ ДАННЫЕ ПРОГНОЗА ДЛЯ КОНСИСТЕНТНОСТИ
            if i == 0:
                # Используем данные прогноза для текущего часа (такие же как в /weather)
                current_hour_forecast = WeatherFormatter.get_current_hour_forecast(weather_data)
                if current_hour_forecast:
                    condition = current_hour_forecast['condition']['text']
                    is_day = current_hour_forecast['is_day'] == 1
                    temp = current_hour_forecast['temp_c']
                    feels_like = current_hour_forecast['feelslike_c']
                    wind_speed = current_hour_forecast['wind_kph']
                    wind_dir = current_hour_forecast['wind_degree']
                    chance_of_rain = current_hour_forecast.get('chance_of_rain', 0)
                else:
                    # Запасной вариант
                    condition = hour_data['condition']['text']
                    is_day = hour_data['is_day'] == 1
                    temp = hour_data['temp_c']
                    feels_like = hour_data['feelslike_c']
                    wind_speed = hour_data['wind_kph']
                    wind_dir = hour_data['wind_degree']
                    chance_of_rain = hour_data.get('chance_of_rain', 0)
            else:
                # Для остальных часов используем прогнозные данные
                condition = hour_data['condition']['text']
                is_day = hour_data['is_day'] == 1
                temp = hour_data['temp_c']
                feels_like = hour_data['feelslike_c']
                wind_speed = hour_data['wind_kph']
                wind_dir = hour_data['wind_degree']
                chance_of_rain = hour_data.get('chance_of_rain', 0)
            
            emoji = WeatherIcons.get_condition_emoji(condition, is_day)
            
            # Форматируем время
            if i == 0:
                time_str = "Сейчас"
            else:
                # Для часов следующего дня добавляем маркер
                if hour_time.date() > local_time.date():
                    time_str = hour_time.strftime('%H:%M') + "🌙"
                else:
                    time_str = hour_time.strftime('%H:%M')
            
            temp_text = f"{temp:.0f}°({feels_like:.0f}°)"
            precip_text = f"{chance_of_rain}%" if chance_of_rain > 0 else " - "
            wind_direction = WeatherIcons.get_wind_direction(wind_dir)
            wind_display = f"{wind_speed:.0f}{wind_direction}"
            
            # Форматируем строку таблицы
            line = f"│ {time_str:^8} │ {emoji:^6} │ {temp_text:^11} │ {precip_text:^6} │ {wind_display:^6} │"
            lines.append(line)
        
        lines.extend([
            "└──────────┴────────┴─────────────┴────────┴────────┘",
            "",
            "**📋 ОБОЗНАЧЕНИЯ:**",
            "• **Температура** - фактическая °C (ощущается как °C)",
            "• **Осадки** - вероятность дождя в %", 
            "• **Ветер** - скорость (км/ч) + направление",
            "• **🌙** - следующий день"
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_recommendations(temp, feels_like, humidity, wind_speed, uv_index, precip_mm, visibility):
        """Генерация рекомендаций"""
        recommendations = []
        
        # Одежда
        if feels_like > 25:
            recommendations.append("• 👕 Очень легкая одежда, головной убор обязателен")
        elif feels_like > 20:
            recommendations.append("• 👕 Легкая одежда, возможен головной убор")
        elif feels_like > 15:
            recommendations.append("• 👔 Легкая куртка или кофта")
        elif feels_like > 10:
            recommendations.append("• 🧥 Демисезонная куртка")
        elif feels_like > 5:
            recommendations.append("• 🧥 Теплая куртка, шапка")
        elif feels_like > 0:
            recommendations.append("• 🧣 Зимняя куртка, шапка, шарф")
        else:
            recommendations.append("• 🧣 Теплая зимняя одежда, шапка, перчатки, шарф")
        
        # Зонт
        if precip_mm > 10:
            recommendations.append("• 🌂 Обязательно возьмите зонт и дождевик")
        elif precip_mm > 5:
            recommendations.append("• 🌂 Рекомендуется зонт")
        elif precip_mm > 0:
            recommendations.append("• 🌂 Возможны кратковременные осадки")
        
        # Защита от солнца
        if uv_index > 7:
            recommendations.append("• 😎 Обязательно используйте крем SPF 50+")
        elif uv_index > 5:
            recommendations.append("• 😎 Рекомендуется крем SPF 30+")
        
        # Ветер
        if wind_speed > 40:
            recommendations.append("• 💨 Очень сильный ветер - будьте осторожны")
        elif wind_speed > 30:
            recommendations.append("• 💨 Сильный ветер - одежда не должна развеваться")
        
        return recommendations

class SevenDayForecastFormatter:
    """Форматирование 7-дневного прогноза (компактная версия)"""
    
    WEATHER_EMOJIS = {
        0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️', 45: '🌫️', 48: '🌫️',
        51: '🌦️', 53: '🌦️', 55: '🌦️', 61: '🌧️', 63: '🌧️', 65: '🌧️',
        80: '🌦️', 81: '🌧️', 82: '⛈️', 95: '⛈️', 96: '⛈️➕', 99: '⛈️➕'
    }
    
    WEEKDAY_NAMES = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
    
    @staticmethod
    def format_7day_forecast(forecast_data, city_name):
        """Компактный формат 7-дневного прогноза"""
        if not forecast_data or 'daily' not in forecast_data:
            return "❌ Не удалось получить данные прогноза"
        
        daily = forecast_data['daily']
        times = daily['time'][1:8]  # Исключаем сегодня
        
        lines = [
            f"📅 **ПРОГНОЗ НА 7 ДНЕЙ - {city_name.upper()}**",
            "",
            "┌────────┬────────┬─────────────┬────────┬────────┐"