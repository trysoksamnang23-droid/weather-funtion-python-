import tkinter as tk
import requests
from PIL import Image, ImageTk, ImageDraw
import time

BG_GRADIENT_START = "#1F2937"
BG_GRADIENT_END = "#111827"
CARD_BG = "#1F2937"
TEXT_MAIN = "#F9FAFB"
TEXT_MUTED = "#9CA3AF"
ICON_CIRCLE_BG = "#374151"

WMO_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "☀️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Drizzle", "🌧️"),
    53: ("Drizzle", "🌧️"),
    55: ("Dense drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    80: ("Rain showers", "🌧️"),
    95: ("Thunderstorm", "⛈️"),
}


def create_smooth_circle(size, bg_color):
    scale = 4
    large_size = size * scale
    img = Image.new("RGBA", (large_size, large_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(0, 0), (large_size - 1, large_size - 1)], fill=bg_color)
    return img.resize((size, size), Image.Resampling.LANCZOS)


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
        self.title("Weather")
        self.geometry("380x670")
        self.resizable(False, False)
        self.configure(bg="#111827")

        self.use_fahrenheit = True  # Set True to match Google Weather by default

        self.canvas = tk.Canvas(self, width=380, height=670, bg="#111827", bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.bg_pil = create_rounded_gradient(360, 650, 45, BG_GRADIENT_START, BG_GRADIENT_END)
        self.bg_img = ImageTk.PhotoImage(self.bg_pil)
        self.canvas.create_image(10, 10, image=self.bg_img, anchor="nw")

        self.canvas.create_text(190, 45, text="Weather in", font=("Segoe UI", 26, "bold"), fill="#9CA3AF")

        self.search_entry = tk.Entry(self, font=("Segoe UI", 12), bg="#374151", fg=TEXT_MAIN,
                                     insertbackground="white", bd=0, justify="center", highlightthickness=0)
        self.search_entry.bind("<Return>", self.fetch_weather)
        self.canvas.create_window(190, 90, window=self.search_entry, width=240, height=34)

        # Unit Toggle Button (°F / °C)
        self.unit_btn = tk.Button(self, text="°F", font=("Segoe UI", 10, "bold"), bg="#374151", fg=TEXT_MAIN,
                                  bd=0, activebackground="#4B5563", activeforeground="white", command=self.toggle_units)
        self.canvas.create_window(320, 90, window=self.unit_btn, width=35, height=34)

        self.clock_lbl = tk.Label(self, text="", font=("Segoe UI", 11, "bold"), fg=TEXT_MUTED, bg="#18202F")
        self.canvas.create_window(190, 625, window=self.clock_lbl)

        self.card_target_y = 135
        self.card_current_y = 135

        self.build_weather_card()
        self.animate_pulse()
        self.update_clock()

    def toggle_units(self):
        self.use_fahrenheit = not self.use_fahrenheit
        self.unit_btn.config(text="°F" if self.use_fahrenheit else "°C")
        if self.search_entry.get().strip():
            self.fetch_weather()

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

        self.feels_val = tk.Label(self, text="--°", font=("Segoe UI Light", 26), fg=TEXT_MAIN, bg=CARD_BG)
        self.feels_lbl = tk.Label(self, text="Feels Like", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG)
        self.humidity_val = tk.Label(self, text="--%", font=("Segoe UI Light", 26), fg=TEXT_MAIN, bg=CARD_BG)
        self.humidity_lbl = tk.Label(self, text="Humidity", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG)

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
            (self.feels_val, 115, 325, "center"),
            (self.feels_lbl, 115, 355, "center"),
            (self.humidity_val, 265, 325, "center"),
            (self.humidity_lbl, 265, 355, "center"),
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

    def fetch_weather(self, event=None):
        query = self.search_entry.get().strip()
        if not query:
            return

        self.card_current_y = 190
        self.animate_slide_up()

        try:
            # 1. Geocoding Query
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=1&language=en&format=json"
            geo_res = requests.get(geo_url, timeout=5).json()

            if not geo_res.get("results"):
                self.city_lbl.config(text="Not Found")
                return

            location = geo_res["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            city_name = location["name"]
            country = location.get("country_code", "").upper()

            # 2. Select Units
            unit_param = "&temperature_unit=fahrenheit" if self.use_fahrenheit else ""
            unit_symbol = "°F" if self.use_fahrenheit else "°C"

            # 3. Fetch Forecast
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code&daily=temperature_2m_max,temperature_2m_min&timezone=auto{unit_param}"
            res = requests.get(weather_url, timeout=5).json()

            current = res["current"]
            daily = res["daily"]

            temp = round(current["temperature_2m"])
            feels_like = round(current["apparent_temperature"])
            humidity = current["relative_humidity_2m"]
            code = current["weather_code"]

            max_temp = round(daily["temperature_2m_max"][0])
            min_temp = round(daily["temperature_2m_min"][0])

            cond_desc, emoji = WMO_CODES.get(code, ("Cloudy", "☁️"))

            # Update Labels
            self.city_lbl.config(text=f"{city_name}, {country}" if country else city_name)
            self.temp_lbl.config(text=f"{temp}{unit_symbol}")
            self.cond_lbl.config(text=cond_desc.replace(" ", "\n"))
            self.max_lbl.config(text=f"Max: {max_temp}{unit_symbol}")
            self.min_lbl.config(text=f"Min: {min_temp}{unit_symbol}")
            self.emoji_lbl.config(text=emoji)
            self.feels_val.config(text=f"{feels_like}{unit_symbol}")
            self.humidity_val.config(text=f"{humidity}%")

        except Exception as err:
            self.city_lbl.config(text="Error")
            print("Fetch error:", err)


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()