import datetime
import threading
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk
import requests

BG_GRADIENT_START = "#1F2937"
BG_GRADIENT_END = "#111827"
CARD_BG = "#1F2937"
TEXT_MAIN = "#F9FAFB"
TEXT_MUTED = "#9CA3AF"
ICON_CIRCLE_BG = "#374151"

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
    3: ("Overcast", "☁️"), 45: ("Foggy", "🌫️"), 48: ("Rime fog", "🌫️"),
    51: ("Light drizzle", "🌧️"), 53: ("Drizzle", "🌧️"), 55: ("Dense drizzle", "🌧️"),
    56: ("Freezing drizzle", "🌧️"), 57: ("Freezing drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"), 63: ("Moderate rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    66: ("Freezing rain", "🌧️"), 67: ("Freezing rain", "🌧️"),
    71: ("Slight snow", "❄️"), 73: ("Moderate snow", "❄️"), 75: ("Heavy snow", "❄️"),
    80: ("Rain showers", "🌧️"), 81: ("Rain showers", "🌧️"), 82: ("Heavy showers", "🌧️"),
    95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm", "⛈️"), 99: ("Thunderstorm", "⛈️")
}


def create_smooth_circle(size, bg_color):
    scale = 2
    large_size = size * scale
    img = Image.new("RGBA", (large_size, large_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(0, 0), (large_size - 1, large_size - 1)], fill=bg_color)
    return img.resize((size, size), Image.Resampling.BILINEAR)


def create_rounded_gradient(width, height, radius, color1, color2):
    scale = 2
    w_scale, h_scale = width * scale, height * scale
    base = Image.new("RGBA", (w_scale, h_scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)

    r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
    r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

    for y in range(h_scale):
        ratio = y / h_scale
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (w_scale, y)], fill=(r, g, b, 255))

    mask = Image.new("L", (w_scale, h_scale), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (w_scale - 1, h_scale - 1)], radius=radius * scale, fill=255)
    base.putalpha(mask)

    return base.resize((width, height), Image.Resampling.LANCZOS)


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cambodia Weather")
        self.geometry("380x670")
        self.resizable(False, False)
        self.configure(bg="#111827")

        self.use_fahrenheit = False
        self.current_location_data = None

        self.canvas = tk.Canvas(self, width=380, height=670, bg="#111827", bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.bg_pil = create_rounded_gradient(360, 650, 45, BG_GRADIENT_START, BG_GRADIENT_END)
        self.bg_img = ImageTk.PhotoImage(self.bg_pil)
        self.canvas.create_image(10, 10, image=self.bg_img, anchor="nw")

        self.header_title = self.canvas.create_text(190, 45, text="Provinces", font=("Segoe UI", 22, "bold"),
                                                    fill="#9CA3AF")

        self.unit_btn = tk.Button(self, text="°C", font=("Segoe UI", 10, "bold"), bg="#374151", fg=TEXT_MAIN,
                                  bd=0, activebackground="#4B5563", activeforeground="white", command=self.toggle_units)
        self.canvas.create_window(320, 45, window=self.unit_btn, width=35, height=30)

        self.back_btn = tk.Button(self, text="📋 List", font=("Segoe UI", 10, "bold"), bg="#374151", fg=TEXT_MAIN,
                                  bd=0, activebackground="#4B5563", activeforeground="white", command=self.show_list)
        self.back_btn_window = self.canvas.create_window(60, 45, window=self.back_btn, width=65, height=30)
        self.canvas.itemconfigure(self.back_btn_window, state="hidden")

        self.clock_lbl = tk.Label(self, text="", font=("Segoe UI", 11, "bold"), fg=TEXT_MUTED, bg="#18202F")
        self.canvas.create_window(190, 625, window=self.clock_lbl)

        self.card_target_y = 135
        self.card_current_y = 700

        self.build_weather_card()
        self.build_province_list()
        self.animate_pulse()
        self.update_clock()

    def _on_mousewheel(self, event):
        if event.delta:
            self.list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            self.list_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.list_canvas.yview_scroll(1, "units")

    def bind_scroll_events(self):
        self.list_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.list_canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.list_canvas.bind_all("<Button-5>", self._on_mousewheel)

    def unbind_scroll_events(self):
        self.list_canvas.unbind_all("<MouseWheel>")
        self.list_canvas.unbind_all("<Button-4>")
        self.list_canvas.unbind_all("<Button-5>")

    def build_province_list(self):
        self.list_frame = tk.Frame(self, bg="#1F2937", bd=0)

        self.list_canvas = tk.Canvas(self.list_frame, bg="#1F2937", bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.list_canvas.yview)
        scrollable_frame = tk.Frame(self.list_canvas, bg="#1F2937")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))
        )

        canvas_window = self.list_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        self.list_canvas.bind(
            "<Configure>",
            lambda e: self.list_canvas.itemconfig(canvas_window, width=e.width)
        )

        self.list_canvas.configure(yscrollcommand=scrollbar.set)
        self.bind_scroll_events()

        for prov in PROVINCES:
            btn = tk.Button(
                scrollable_frame,
                text=f"📍  {prov['name']}",
                font=("Segoe UI", 11, "bold"),
                bg="#374151",
                fg=TEXT_MAIN,
                anchor="w",
                padx=15,
                pady=8,
                bd=0,
                activebackground="#059669",
                activeforeground="white",
                command=lambda p=prov: self.select_location(p)
            )
            btn.pack(fill="x", pady=3, padx=5)

        self.list_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.list_window = self.canvas.create_window(190, 335, window=self.list_frame, width=320, height=480)

    def show_list(self):
        self.card_current_y = 700
        self.canvas.coords(self.card_window, 40, self.card_current_y)
        self.canvas.coords(self.w_icon_bg, 135, self.card_current_y + 180)

        for item_id, offset_y in self.card_elements:
            curr_x = self.canvas.coords(item_id)[0]
            self.canvas.coords(item_id, curr_x, self.card_current_y + offset_y)

        self.canvas.itemconfigure(self.list_window, state="normal")
        self.canvas.itemconfig(self.header_title, text="Provinces")
        self.canvas.itemconfigure(self.back_btn_window, state="hidden")
        self.bind_scroll_events()

    def select_location(self, prov):
        self.unbind_scroll_events()
        self.canvas.itemconfigure(self.list_window, state="hidden")
        self.canvas.itemconfig(self.header_title, text="Weather")
        self.canvas.itemconfigure(self.back_btn_window, state="normal")

        self.current_location_data = (prov["name"], prov["lat"], prov["lon"])
        self.city_lbl.config(text=prov["name"])
        self.temp_lbl.config(text="--°")
        self.cond_lbl.config(text="Loading...")

        self.card_current_y = 600
        self.animate_slide_up()
        self.fetch_weather_async(prov["name"], prov["lat"], prov["lon"])

    def toggle_units(self):
        self.use_fahrenheit = not self.use_fahrenheit
        self.unit_btn.config(text="°F" if self.use_fahrenheit else "°C")
        if self.current_location_data:
            name, lat, lon = self.current_location_data
            self.fetch_weather_async(name, lat, lon)

    def build_weather_card(self):
        scale = 2
        card_large = Image.new("RGBA", (300 * scale, 430 * scale), (0, 0, 0, 0))
        ImageDraw.Draw(card_large).rounded_rectangle([(0, 0), (300 * scale - 1, 430 * scale - 1)], radius=35 * scale,
                                                     fill=CARD_BG)
        self.card_img = ImageTk.PhotoImage(card_large.resize((300, 430), Image.Resampling.LANCZOS))
        self.card_window = self.canvas.create_image(40, self.card_current_y, image=self.card_img, anchor="nw")

        self.city_lbl = tk.Label(self, text="", font=("Segoe UI", 18, "bold"), fg=TEXT_MAIN, bg=CARD_BG)
        self.dots_lbl = tk.Label(self, text="• • •", font=("Segoe UI", 10), fg="#4B5563", bg=CARD_BG)
        self.temp_lbl = tk.Label(self, text="--°", font=("Segoe UI Light", 42), fg=TEXT_MAIN, bg=CARD_BG)
        self.cond_lbl = tk.Label(self, text="--", font=("Segoe UI", 11, "bold"), fg=TEXT_MAIN, bg=CARD_BG,
                                 justify="right")
        self.max_lbl = tk.Label(self, text="Max: --°", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG,
                                justify="right")
        self.min_lbl = tk.Label(self, text="Min: --°", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG,
                                justify="right")

        self.feels_val = tk.Label(self, text="--°", font=("Segoe UI Light", 22), fg=TEXT_MAIN, bg=CARD_BG)
        self.feels_lbl = tk.Label(self, text="Feels Like", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=CARD_BG)

        self.predict_icon = tk.Label(self, text="", font=("Segoe UI Emoji", 16), bg=CARD_BG, fg="white")
        self.predict_val = tk.Label(self, text="--°", font=("Segoe UI Light", 22), fg=TEXT_MAIN, bg=CARD_BG)
        self.predict_lbl = tk.Label(self, text="In 1 Hour", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=CARD_BG)

        self.humidity_val = tk.Label(self, text="--%", font=("Segoe UI Light", 22), fg=TEXT_MAIN, bg=CARD_BG)
        self.humidity_lbl = tk.Label(self, text="Humidity", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=CARD_BG)

        self.base_circle_size = 110
        self.current_circle_size = 110
        self.pulse_direction = 0.3

        self.icon_circle_pil = create_smooth_circle(self.base_circle_size, ICON_CIRCLE_BG)
        self.icon_img = ImageTk.PhotoImage(self.icon_circle_pil)
        self.w_icon_bg = self.canvas.create_image(135, self.card_current_y + 180, image=self.icon_img, anchor="nw")

        self.emoji_lbl = tk.Label(self, text="☁️", font=("Segoe UI Emoji", 38), bg=ICON_CIRCLE_BG, fg="white")

        elements_def = [
            (self.city_lbl, 190, 30, "center"),
            (self.dots_lbl, 190, 53, "center"),
            (self.temp_lbl, 115, 120, "center"),
            (self.cond_lbl, 245, 100, "e"),
            (self.max_lbl, 245, 130, "e"),
            (self.min_lbl, 245, 150, "e"),
            (self.emoji_lbl, 190, 235, "center"),
            (self.feels_val, 90, 325, "center"),
            (self.feels_lbl, 90, 355, "center"),
            (self.predict_icon, 168, 325, "e"),
            (self.predict_val, 172, 325, "w"),
            (self.predict_lbl, 190, 355, "center"),
            (self.humidity_val, 290, 325, "center"),
            (self.humidity_lbl, 290, 355, "center"),
        ]

        self.card_elements = []
        for widget, x, offset_y, anchor in elements_def:
            item_id = self.canvas.create_window(x, self.card_current_y + offset_y, window=widget, anchor=anchor)
            self.card_elements.append((item_id, offset_y))

    def update_clock(self):
        self.clock_lbl.config(text=time.strftime("%I:%M:%S %p"))
        self.after(1000, self.update_clock)

    def animate_slide_up(self):
        if self.card_current_y > self.card_target_y:
            dy = max(1, (self.card_current_y - self.card_target_y) * 0.25)
            self.card_current_y -= dy

            self.canvas.coords(self.card_window, 40, self.card_current_y)
            self.canvas.coords(self.w_icon_bg, 135, self.card_current_y + 180)

            for item_id, offset_y in self.card_elements:
                curr_x = self.canvas.coords(item_id)[0]
                self.canvas.coords(item_id, curr_x, self.card_current_y + offset_y)

            self.after(16, self.animate_slide_up)

    def animate_pulse(self):
        if self.current_circle_size >= 114:
            self.pulse_direction = -0.3
        elif self.current_circle_size <= 106:
            self.pulse_direction = 0.3

        self.current_circle_size += self.pulse_direction
        size_int = int(self.current_circle_size)

        self.icon_circle_pil = create_smooth_circle(size_int, ICON_CIRCLE_BG)
        self.icon_img = ImageTk.PhotoImage(self.icon_circle_pil)
        self.canvas.itemconfig(self.w_icon_bg, image=self.icon_img)

        offset = (self.base_circle_size - size_int) // 2
        self.canvas.coords(self.w_icon_bg, 135 + offset, self.card_current_y + 180 + offset)

        self.after(50, self.animate_pulse)

    def fetch_weather_async(self, city_name, lat, lon):
        threading.Thread(target=self._worker_fetch, args=(city_name, lat, lon), daemon=True).start()

    def _worker_fetch(self, city_name, lat, lon):
        try:
            unit_param = "&temperature_unit=fahrenheit" if self.use_fahrenheit else ""
            unit_symbol = "°F" if self.use_fahrenheit else "°C"

            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code"
                f"&hourly=temperature_2m,weather_code"
                f"&daily=temperature_2m_max,temperature_2m_min"
                f"&timezone=auto{unit_param}"
            )
            res = requests.get(weather_url, timeout=5).json()

            current, daily = res["current"], res["daily"]
            temp = round(current["temperature_2m"])
            feels_like = round(current["apparent_temperature"])
            humidity = current["relative_humidity_2m"]
            code = current["weather_code"]

            max_temp = round(daily["temperature_2m_max"][0])
            min_temp = round(daily["temperature_2m_min"][0])
            cond_desc, emoji = WMO_CODES.get(code, ("Cloudy", "☁️"))

            current_time_str = current.get("time")
            hourly_times = res["hourly"].get("time", [])

            if current_time_str in hourly_times:
                current_idx = hourly_times.index(current_time_str)
                next_idx = min(current_idx + 1, len(hourly_times) - 1)
            else:
                next_idx = 1

            future_temp = round(res["hourly"]["temperature_2m"][next_idx])
            future_code = res["hourly"]["weather_code"][next_idx]
            _, future_emoji = WMO_CODES.get(future_code, ("Cloudy", "☁️"))

            self.after(0, lambda: self._apply_weather_data(
                f"{city_name}, KH", temp, feels_like, humidity, max_temp, min_temp,
                cond_desc, emoji, unit_symbol, future_temp, future_emoji
            ))
        except Exception as err:
            print("Fetch error:", err)
            self.after(0, lambda: self.city_lbl.config(text="Connection Error"))

    def _apply_weather_data(self, location_text, temp, feels_like, humidity, max_temp, min_temp,
                            cond_desc, emoji, unit_symbol, future_temp, future_emoji):
        self.city_lbl.config(text=location_text)
        self.temp_lbl.config(text=f"{temp}{unit_symbol}")
        self.cond_lbl.config(text=cond_desc.replace(" ", "\n"))
        self.max_lbl.config(text=f"Max: {max_temp}{unit_symbol}")
        self.min_lbl.config(text=f"Min: {min_temp}{unit_symbol}")
        self.emoji_lbl.config(text=emoji)
        self.feels_val.config(text=f"{feels_like}{unit_symbol}")
        self.predict_icon.config(text=future_emoji)
        self.predict_val.config(text=f"{future_temp}{unit_symbol}")
        self.humidity_val.config(text=f"{humidity}%")


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()