import datetime
import threading
import requests
from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineIconListItem, IconLeftWidget
from kivymd.uix.screen import MDScreen

KV = '''
MDScreenManager:
    ListScreen:
    WeatherScreen:

<ListScreen>:
    name: "list"
    MDFloatLayout:
        md_bg_color: 0.07, 0.09, 0.15, 1

        MDLabel:
            text: "Provinces"
            font_style: "H5"
            bold: True
            theme_text_color: "Custom"
            text_color: 0.61, 0.64, 0.69, 1
            pos_hint: {"center_x": 0.5, "top": 0.95}
            halign: "center"

        MDRaisedButton:
            id: unit_btn
            text: "°F"
            pos_hint: {"right": 0.95, "top": 0.96}
            md_bg_color: 0.22, 0.25, 0.32, 1
            on_release: app.toggle_units()

        ScrollView:
            pos_hint: {"top": 0.88}
            size_hint_y: 0.88
            MDList:
                id: province_list

<WeatherScreen>:
    name: "weather"
    MDFloatLayout:
        md_bg_color: 0.07, 0.09, 0.15, 1

        MDIconButton:
            icon: "arrow-left"
            pos_hint: {"x": 0.02, "top": 0.96}
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            on_release: app.show_list()

        MDLabel:
            text: "Weather"
            font_style: "H5"
            bold: True
            theme_text_color: "Custom"
            text_color: 0.61, 0.64, 0.69, 1
            pos_hint: {"center_x": 0.5, "top": 0.95}
            halign: "center"

        MDCard:
            size_hint: 0.85, 0.7
            pos_hint: {"center_x": 0.5, "center_y": 0.45}
            radius: [25,]
            md_bg_color: 0.12, 0.16, 0.22, 1
            orientation: "vertical"
            padding: "20dp"
            spacing: "10dp"

            MDLabel:
                id: city_lbl
                text: "Loading..."
                font_style: "H5"
                bold: True
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1

            MDLabel:
                id: emoji_lbl
                text: "☁️"
                font_style: "H2"
                halign: "center"

            MDLabel:
                id: temp_lbl
                text: "--°"
                font_style: "H3"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1

            MDLabel:
                id: cond_lbl
                text: "--"
                font_style: "Subtitle1"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.61, 0.64, 0.69, 1

            MDFloatLayout:
                size_hint_y: 0.4

                MDLabel:
                    id: feels_lbl
                    text: "Feels Like\\n--"
                    halign: "center"
                    pos_hint: {"center_x": 0.2, "center_y": 0.5}
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1

                MDLabel:
                    id: predict_lbl
                    text: "In 1 Hour\\n--"
                    halign: "center"
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1

                MDLabel:
                    id: humidity_lbl
                    text: "Humidity\\n--"
                    halign: "center"
                    pos_hint: {"center_x": 0.8, "center_y": 0.5}
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
'''

PROVINCES = [
    {"name": "Banteay Meanchey", "lat": 13.7532, "lon": 102.9896},
    {"name": "Battambang", "lat": 13.1027, "lon": 103.1982},
    {"name": "Kampong Cham", "lat": 12.0983, "lon": 105.3131},
    {"name": "Kampong Chhnang", "lat": 12.2500, "lon": 104.6667},
    {"name": "Kampong Speu", "lat": 11.6155, "lon": 104.3792},
    {"name": "Kampong Thom", "lat": 12.8167, "lon": 103.8413},
    {"name": "Kampot", "lat": 10.7325, "lon": 104.3792},
    {"name": "Kandal", "lat": 11.2237, "lon": 105.1259},
    {"name": "Kep", "lat": 10.4828, "lon": 104.3167},
    {"name": "Koh Kong", "lat": 11.5763, "lon": 103.3587},
    {"name": "Kratie", "lat": 12.5044, "lon": 105.9700},
    {"name": "Mondulkiri", "lat": 12.7879, "lon": 107.1012},
    {"name": "Oddar Meanchey", "lat": 14.1610, "lon": 103.8216},
    {"name": "Pailin", "lat": 12.8489, "lon": 102.6093},
    {"name": "Phnom Penh", "lat": 11.5564, "lon": 104.9282},
    {"name": "Preah Sihanouk", "lat": 10.6093, "lon": 103.5296},
    {"name": "Preah Vihear", "lat": 14.0086, "lon": 104.8455},
    {"name": "Prey Veng", "lat": 11.3802, "lon": 105.5005},
    {"name": "Pursat", "lat": 12.2721, "lon": 103.7289},
    {"name": "Ratanakiri", "lat": 13.8577, "lon": 107.1012},
    {"name": "Siem Reap", "lat": 13.3618, "lon": 103.8606},
    {"name": "Stung Treng", "lat": 13.5765, "lon": 105.9700},
    {"name": "Svay Rieng", "lat": 11.1427, "lon": 105.8290},
    {"name": "Takeo", "lat": 10.9322, "lon": 104.7988},
    {"name": "Tboung Khmum", "lat": 11.8891, "lon": 105.8760},
]

WMO_CODES = {
    0: ("Clear sky", "☀️"), 1: ("Mainly clear", "☀️"), 2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Foggy", "🌫️"), 51: ("Light drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"), 80: ("Rain showers", "🌧️"), 95: ("Thunderstorm", "⛈️")
}


class ListScreen(MDScreen):
    pass


class WeatherScreen(MDScreen):
    pass


class CambodiaWeatherApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.use_fahrenheit = True
        self.current_prov = None
        return Builder.load_string(KV)

    def on_start(self):
        list_widget = self.root.get_screen("list").ids.province_list
        for prov in PROVINCES:
            item = OneLineIconListItem(
                text=prov["name"],
                on_release=lambda x, p=prov: self.select_location(p)
            )
            item.add_widget(IconLeftWidget(icon="map-marker"))
            list_widget.add_widget(item)

    def toggle_units(self):
        self.use_fahrenheit = not self.use_fahrenheit
        unit_text = "°F" if self.use_fahrenheit else "°C"
        self.root.get_screen("list").ids.unit_btn.text = unit_text
        if self.current_prov:
            self.fetch_weather(self.current_prov)

    def show_list(self):
        self.root.current = "list"

    def select_location(self, prov):
        self.current_prov = prov
        self.root.current = "weather"
        self.fetch_weather(prov)

    def fetch_weather(self, prov):
        threading.Thread(target=self._worker_fetch, args=(prov,), daemon=True).start()

    def _worker_fetch(self, prov):
        try:
            unit_param = "&temperature_unit=fahrenheit" if self.use_fahrenheit else ""
            unit_symbol = "°F" if self.use_fahrenheit else "°C"

            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={prov['lat']}&longitude={prov['lon']}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code"
                f"&hourly=temperature_2m,weather_code&timezone=auto{unit_param}"
            )
            res = requests.get(url, timeout=5).json()
            curr = res["current"]

            temp = round(curr["temperature_2m"])
            feels = round(curr["apparent_temperature"])
            humidity = curr["relative_humidity_2m"]
            cond, emoji = WMO_CODES.get(curr["weather_code"], ("Cloudy", "☁️"))

            # 1-hour prediction logic
            next_hour = (datetime.datetime.now().hour + 1) % 24
            future_temp = round(res["hourly"]["temperature_2m"][next_hour])
            future_code = res["hourly"]["weather_code"][next_hour]
            _, future_emoji = WMO_CODES.get(future_code, ("Cloudy", "☁️"))

            Clock.schedule_once(
                lambda dt: self.update_ui(prov["name"], temp, feels, humidity, cond, emoji, unit_symbol, future_temp,
                                          future_emoji)
            )
        except Exception as e:
            print(e)

    def update_ui(self, name, temp, feels, humidity, cond, emoji, unit_symbol, future_temp, future_emoji):
        screen = self.root.get_screen("weather")
        screen.ids.city_lbl.text = name
        screen.ids.emoji_lbl.text = emoji
        screen.ids.temp_lbl.text = f"{temp}{unit_symbol}"
        screen.ids.cond_lbl.text = cond
        screen.ids.feels_lbl.text = f"Feels Like\n{feels}{unit_symbol}"
        screen.ids.predict_lbl.text = f"In 1 Hour\n{future_emoji} {future_temp}{unit_symbol}"
        screen.ids.humidity_lbl.text = f"Humidity\n{humidity}%"


if __name__ == "__main__":
    CambodiaWeatherApp().run()