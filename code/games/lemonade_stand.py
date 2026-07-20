import random
import config as cfg
import hal
from game_base import Game, EXIT
from widgets import NumberPicker, ConfirmDialog, draw_wrapped, ProgressBar

class Weather:
    def __init__(self, name, multiplier, description, color):
        self.name = name
        self.multiplier = multiplier
        self.description = description
        self.color = color


class Season:
    def __init__(self, name, start_day, end_day, base_multiplier, color, description):
        self.name = name
        self.start_day = start_day
        self.end_day = end_day
        self.base_multiplier = base_multiplier
        self.color = color
        self.description = description


class Event:
    def __init__(self, name, description, effect, multiplier, supply_loss):
        self.name = name
        self.description = description
        self.effect = effect
        self.multiplier = multiplier
        self.supply_loss = supply_loss


class Prices:
    def __init__(self):
        self.lemons = 0.02
        self.sugar = 0.04
        self.glasses = 0.01
        self.signs = 0.15

SEASONS = [
    Season("Early Summer", 1, 20, 1.10, cfg.COLOR_YELLOW,
           "School's out and the sun is blazing."),
    Season("High Summer", 21, 45, 1.25, cfg.COLOR_ORANGE,
           "The hottest stretch of the year. Business is booming."),
    Season("Late Summer", 46, 65, 1.00, cfg.COLOR_ORANGE,
           "The heat is easing off. Steady traffic."),
    Season("Early Autumn", 66, 80, 0.80, cfg.COLOR_GRAY,
           "Leaves are turning. Fewer cold-drink customers."),
    Season("Deep Autumn", 81, 100, 0.55, cfg.COLOR_DARK_GRAY,
           "It's chilly. Only the loyal customers show up."),
]

WEATHERS = [
    Weather("Scorching Hot", 1.8, "A heatwave! Desperate for cold drinks.", cfg.COLOR_RED),
    Weather("Sunny & Warm", 1.3, "Beautiful sunny day. Great weather!", cfg.COLOR_YELLOW),
    Weather("Partly Cloudy", 1.0, "Some clouds but still pleasant.", cfg.COLOR_WHITE),
    Weather("Overcast", 0.75, "Grey skies. Fewer people out.", cfg.COLOR_GRAY),
    Weather("Rainy", 0.35, "Raining. Hardly anyone comes out.", cfg.COLOR_BLUE),
    Weather("Perfect Breeze", 1.15, "A warm breeze - ideal for lemonade.", cfg.COLOR_CYAN),
]

EVENTS_TEMPLATES = [
    Event("Street Festival", "A festival is happening nearby!", "+CROWD", 2.0, {}),
    Event("School Field Trip", "Kids from the local school walked by!", "+KIDS", 1.6, {}),
    Event("Road Closure", "The road near your stand is closed.", "-ROAD", 0.4, {}),
    Event("Lemon Shortage", "Lemons cost double today.", "LEMONS x2", 1.0,
          {"lemons_price_mult": 2.0}),
    Event("Sugar Shortage", "Sugar costs extra today.", "SUGAR x2", 1.0,
          {"sugar_price_mult": 2.0}),
    Event("Ants in Supplies", "Ants got into your storage!", "-LEMONS", 1.0,
          {"lemons": "ROLL_3_8"}),
    Event("Broken Glass", "Some glasses shattered overnight.", "-GLASSES", 1.0,
          {"glasses": "ROLL_5_15"}),
    Event("Health Inspector", "A gold star from the inspector!", "+STAR", 1.3, {}),
    Event("Competition Opens", "A rival stand opened nearby.", "-RIVAL", 0.6, {}),
    Event("Newspaper Feature", "The paper wrote about your stand!", "+PRESS", 1.9, {}),
    Event("Nothing Special", "Just a normal day.", "", 1.0, {}),
    Event("Nothing Special", "A quiet morning.", "", 1.0, {}),
]

REP_TIERS = [
    (86, "Legendary", cfg.COLOR_YELLOW, 1.35),
    (66, "Well-Loved", cfg.COLOR_GREEN, 1.20),
    (46, "Popular", cfg.COLOR_CYAN, 1.00),
    (26, "Recognised", cfg.COLOR_WHITE, 0.90),
    (0, "Unknown", cfg.COLOR_GRAY, 0.75),
]


def get_season(day):
    for s in SEASONS:
        if s.start_day <= day <= s.end_day:
            return s
    return SEASONS[-1]


def rep_tier(rep):
    for threshold, label, color, mult in REP_TIERS:
        if rep >= threshold:
            return label, color, mult
    return REP_TIERS[-1][1], REP_TIERS[-1][2], REP_TIERS[-1][3]


def make_event_instance(template):
    resolved = {}
    for k, v in template.supply_loss.items():
        if v == "ROLL_3_8":
            resolved[k] = random.randint(3, 8)
        elif v == "ROLL_5_15":
            resolved[k] = random.randint(5, 15)
        else:
            resolved[k] = v
    return Event(template.name, template.description, template.effect,
                 template.multiplier, resolved)


BUY_ITEMS = [
    ("lemons", "Lemons", 300),
    ("sugar", "Sugar (cups)", 300),
    ("glasses", "Glasses", 300),
    ("signs", "Signs", 50),
]

RECIPE_LPG, RECIPE_SPG, RECIPE_PRICE = 0, 1, 2


class PricePicker(NumberPicker):

    def draw(self, display):
        display.text(self.label, self.x, self.y, cfg.COLOR_WHITE)
        val_str = f"${self.value / 100:.2f}"
        box_y = self.y + cfg.FONT_H + 10
        display.rect(self.x, box_y, 120, 26, cfg.COLOR_GRAY)
        display.text("<", self.x + 6, box_y + 9, cfg.COLOR_GRAY)
        display.text(val_str, self.x + 40, box_y + 9, cfg.COLOR_HIGHLIGHT)
        display.text(">", self.x + 106, box_y + 9, cfg.COLOR_GRAY)
        display.text("LEFT/RIGHT 1c  UP/DOWN 10c", self.x, box_y + 34, cfg.COLOR_DARK_GRAY)


class LemonadeStand(Game):
    name = "Lemonade Stand"
    description = "Run your own stand, 100 days"

    WIN_CASH = 100.00
    WIN_DAYS = 100
    BROKE_THRESHOLD = 0.10

    def on_enter(self, display, buttons):
        self.buzzer = hal.get_buzzer()
        self.cash = 2.00
        self.day = 1
        self.glasses = 0
        self.lemons = 0
        self.sugar = 0
        self.signs = 0
        self.total_revenue = 0.0
        self.total_sold = 0
        self.prices = Prices()
        self.reputation = 50.0
        self.zero_revenue_streak = 0
        self.history = []
        self.game_over_reason = None
        self.state = "intro"
        self.picker = None
        self.picker_step = None
        self._buy_dialog = None
        self._recipe_dialog = None
        self._eod_data = None

    def _fluctuate_prices(self, event):
        def drift(base, lo=0.8, hi=1.2):
            return round(base * random.uniform(lo, hi), 3)

        lemon_mult = event.supply_loss.get("lemons_price_mult", 1.0)
        sugar_mult = event.supply_loss.get("sugar_price_mult", 1.0)
        self.prices.lemons = max(0.005, drift(0.02) * lemon_mult)
        self.prices.sugar = max(0.005, drift(0.04) * sugar_mult)
        self.prices.glasses = max(0.003, drift(0.01))
        self.prices.signs = max(0.05, drift(0.15))

    def _apply_supply_losses(self, event):
        msgs = []
        if "lemons" in event.supply_loss:
            lost = min(event.supply_loss["lemons"], self.lemons)
            self.lemons -= lost
            if lost:
                msgs.append(f"Lost {lost} lemon(s).")
        if "glasses" in event.supply_loss:
            lost = min(event.supply_loss["glasses"], self.glasses)
            self.glasses -= lost
            if lost:
                msgs.append(f"Lost {lost} glass(es).")
        return msgs

    def _update_reputation(self, lpg, spg, price, sold, customers):
        delta = 0.0
        quality = lpg + spg
        if quality <= 2:
            delta -= 4.0
        elif quality <= 5:
            delta += 2.0
        elif quality <= 7:
            delta += 0.5
        else:
            delta -= 2.0

        fair_price = 0.20
        ratio = price / fair_price
        if ratio <= 0.5:
            delta -= 1.0
        elif ratio <= 1.5:
            delta += 1.5
        elif ratio <= 2.5:
            delta -= 2.0
        else:
            delta -= 5.0

        if customers > 0 and sold < customers:
            delta -= 3.0
        delta -= 0.5
        self.reputation = max(0.0, min(100.0, self.reputation + delta))

    def _simulate_day(self, lpg, spg, price):
        base = random.randint(25, 60)
        customers = int(base * self.weather.multiplier * self.event.multiplier
                        * self.season.base_multiplier)
        customers += self.signs * random.randint(4, 10)
        _, _, rep_mult = rep_tier(self.reputation)
        customers = int(customers * rep_mult)

        if price <= 0.10:
            customers = int(customers * 1.1)
        elif price <= 0.20:
            pass
        elif price <= 0.35:
            customers = int(customers * (0.20 / price) ** 0.7)
        else:
            customers = int(customers * (0.20 / price) ** 1.5)

        quality = lpg + spg
        if quality < 2:
            customers = int(customers * 0.5)
        elif quality <= 4:
            pass
        elif quality <= 6:
            customers = int(customers * 1.15)
        else:
            customers = int(customers * 0.9)
        customers = max(0, customers)

        max_glasses = min(self.lemons // lpg, self.sugar // spg, self.glasses)
        sold = min(customers, max_glasses)
        missed = customers - sold

        self.lemons -= sold * lpg
        self.sugar -= sold * spg
        self.glasses -= sold

        revenue = round(sold * price, 2)
        self.cash += revenue
        self.total_revenue += revenue
        self.total_sold += sold

        self._update_reputation(lpg, spg, price, sold, customers)
        return {"customers": customers, "sold": sold, "revenue": revenue, "missed": missed}

    def _draw_status(self, display):
        display.text(f"Day {self.day}   ${self.cash:.2f}", 12, 8, cfg.COLOR_WHITE)
        display.text(self.season.name, 12, 20, self.season.color)
        inv = f"Lem {self.lemons}  Sug {self.sugar}  Gls {self.glasses}  Sgn {self.signs}"
        display.text(inv, 12, 32, cfg.COLOR_GRAY)
        label, color, _ = rep_tier(self.reputation)
        display.text(f"Rep: {label} ({self.reputation:.0f})", 12, 44, color)
        display.hline(12, 56, cfg.SCREEN_W - 24, cfg.COLOR_DARK_GRAY)

    def _footer(self, display, text):
        display.text(text, 12, cfg.SCREEN_H - 16, cfg.COLOR_DARK_GRAY)

    def _update_intro(self, display, buttons):
        if buttons.pressed("A"):
            self.state = "day_start"
            self._begin_day()
            return None
        if buttons.pressed("B") or buttons.pressed("MENU"):
            return EXIT

        display.fill(cfg.COLOR_BG)
        display.text("LEMONADE STAND", 30, 20, cfg.COLOR_YELLOW)
        display.hline(12, 34, cfg.SCREEN_W - 24, cfg.COLOR_DARK_GRAY)
        y = draw_wrapped(display,
            "Start with $2.00. Buy supplies, set your recipe and price, "
            "and grow your stand.", 12, 48, 26, cfg.COLOR_WHITE)
        y = draw_wrapped(display,
            f"Win: reach ${self.WIN_CASH:.0f} or survive {self.WIN_DAYS} days.",
            12, y + 8, 26, cfg.COLOR_GREEN)
        draw_wrapped(display, "Lose: go bankrupt or can't restock.",
                     12, y + 6, 26, cfg.COLOR_RED)
        self._footer(display, "A Start   B Back to launcher")
        display.show()
        return None

    def _begin_day(self):
        self.season = get_season(self.day)
        self.weather = random.choice(WEATHERS)
        self.event = make_event_instance(random.choice(EVENTS_TEMPLATES))
        self._fluctuate_prices(self.event)
        self.loss_msgs = self._apply_supply_losses(self.event)

    def _update_day_start(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT
        if buttons.pressed("A"):
            self.state = "buying"
            self.buy_qty = [0, 0, 0, 0]
            self.buy_index = 0
            self.picker_step = None
            return None

        display.fill(cfg.COLOR_BG)
        self._draw_status(display)
        y = 68
        display.text(f"Day {self.day} - {self.weather.name}", 12, y, self.weather.color)
        y = draw_wrapped(display, self.weather.description, 12, y + 14, 26,
                         cfg.COLOR_WHITE)

        if self.event.effect or self.event.name != "Nothing Special":
            tag_color = cfg.COLOR_GREEN if self.event.effect.startswith("+") else (
                cfg.COLOR_RED if self.event.effect.startswith("-") else cfg.COLOR_ORANGE)
            display.text(f"Event: {self.event.name}", 12, y + 8, cfg.COLOR_MAGENTA)
            y = draw_wrapped(display, self.event.description, 12, y + 22, 26, cfg.COLOR_WHITE)
            if self.event.effect:
                display.text(f"[{self.event.effect}]", 12, y + 4, tag_color)
                y += 16

        for msg in self.loss_msgs:
            display.text("! " + msg, 12, y + 6, cfg.COLOR_RED)
            y += 12

        self._footer(display, "A Continue to shop   MENU Quit")
        display.show()
        return None

    def _buy_cost_so_far(self):
        total = 0.0
        for i, (attr, _, _) in enumerate(BUY_ITEMS):
            total += self.buy_qty[i] * getattr(self.prices, attr)
        return total

    def _update_buying(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT

        if self.picker_step != self.buy_index:
            attr, label, max_val = BUY_ITEMS[self.buy_index]
            price = getattr(self.prices, attr)
            self.picker = NumberPicker(
                f"{label}  (${price:.3f} each)", value=self.buy_qty[self.buy_index],
                min_val=0, max_val=max_val, step=1, big_step=10,
                x=20, y=90,
            )
            self.picker_step = self.buy_index

        result = self.picker.update(buttons)
        if result is True:
            self.buy_qty[self.buy_index] = self.picker.value
            self.buy_index += 1
            if self.buy_index >= len(BUY_ITEMS):
                cost = self._buy_cost_so_far()
                self.buy_error = cost > self.cash
                self.buy_cost = cost
                self.state = "buy_confirm"
        elif result is False:
            self.buy_qty[self.buy_index] = self.picker.value
            if self.buy_index == 0:
                self.state = "day_start"
            else:
                self.buy_index -= 1

        display.fill(cfg.COLOR_BG)
        self._draw_status(display)
        display.text(f"Shopping ({self.buy_index + 1}/{len(BUY_ITEMS)})", 12, 66,
                     cfg.COLOR_CYAN)
        running = self._buy_cost_so_far()
        if self.picker:
            self.picker.draw(display)
        self._footer(display, "A Next   B Back")
        display.show()
        return None

    def _update_buy_confirm(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT

        if self.buy_error:
            if buttons.pressed("A") or buttons.pressed("B"):
                self.state = "buying"
                self.buy_index = 0
                self.picker_step = None
                return None
            display.fill(cfg.COLOR_BG)
            self._draw_status(display)
            draw_wrapped(display,
                f"Total ${self.buy_cost:.2f} is more than your ${self.cash:.2f}. "
                "Buy less.", 16, 90, 26, cfg.COLOR_RED)
            self._footer(display, "A/B Back to shopping")
            display.show()
            return None

        if self._buy_dialog is None:
            self._buy_dialog = ConfirmDialog(
                f"Buy for ${self.buy_cost:.2f}?", x=16, y=90)

        result = self._buy_dialog.update(buttons)
        display.fill(cfg.COLOR_BG)
        self._draw_status(display)
        self._buy_dialog.draw(display)
        display.show()

        if result is True:
            self.cash -= self.buy_cost
            self.buzzer.beep(700, 50)
            for i, (attr, _, _) in enumerate(BUY_ITEMS):
                setattr(self, attr, getattr(self, attr) + self.buy_qty[i])
            self._buy_dialog = None
            self.state = "recipe"
            self.recipe_step = None
            self.recipe_index = RECIPE_LPG
            self.recipe_lpg = 1
            self.recipe_spg = 1
            self.recipe_price_cents = 20
            return None
        if result is False:
            self._buy_dialog = None
            self.state = "buying"
            self.buy_index = 0
            self.picker_step = None
        return None

    def _update_recipe(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT

        if self.recipe_step != self.recipe_index:
            if self.recipe_index == RECIPE_LPG:
                self.picker = NumberPicker("Lemons per glass", value=self.recipe_lpg,
                                           min_val=1, max_val=5, step=1, big_step=1,
                                           x=24, y=90)
            elif self.recipe_index == RECIPE_SPG:
                self.picker = NumberPicker("Sugar (cups) per glass", value=self.recipe_spg,
                                           min_val=1, max_val=4, step=1, big_step=1,
                                           x=24, y=90)
            else:
                self.picker = PricePicker("Price per glass", value=self.recipe_price_cents,
                                          min_val=1, max_val=200, step=1, big_step=10,
                                          x=24, y=90)
            self.recipe_step = self.recipe_index

        result = self.picker.update(buttons)
        if result is True:
            if self.recipe_index == RECIPE_LPG:
                self.recipe_lpg = self.picker.value
                self.recipe_index = RECIPE_SPG
            elif self.recipe_index == RECIPE_SPG:
                self.recipe_spg = self.picker.value
                self.recipe_index = RECIPE_PRICE
            else:
                self.recipe_price_cents = self.picker.value
                max_batches = min(self.lemons // self.recipe_lpg,
                                  self.sugar // self.recipe_spg, self.glasses)
                self.recipe_error = max_batches == 0
                self.recipe_max_batches = max_batches
                self.state = "recipe_confirm"
        elif result is False:
            if self.recipe_index == RECIPE_LPG:
                self.state = "buying"
                self.buy_index = 0
                self.picker_step = None
            else:
                self.recipe_index -= 1

        display.fill(cfg.COLOR_BG)
        self._draw_status(display)
        display.text(f"Recipe & Price ({self.recipe_index + 1}/3)", 12, 66, cfg.COLOR_CYAN)
        if self.picker:
            self.picker.draw(display)
        self._footer(display, "A Next   B Back")
        display.show()
        return None

    def _update_recipe_confirm(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT

        if self.recipe_error:
            if buttons.pressed("A") or buttons.pressed("B"):
                self.state = "buying"
                self.buy_index = 0
                self.picker_step = None
                return None
            display.fill(cfg.COLOR_BG)
            self._draw_status(display)
            draw_wrapped(display,
                "Not enough supplies to make even one glass with this "
                "recipe. Go buy more.", 16, 90, 26, cfg.COLOR_RED)
            self._footer(display, "A/B Back to shopping")
            display.show()
            return None

        if self._recipe_dialog is None:
            self._recipe_dialog = ConfirmDialog(
                f"Can make {self.recipe_max_batches} glass(es). Looks good?",
                x=16, y=90)

        result = self._recipe_dialog.update(buttons)
        display.fill(cfg.COLOR_BG)
        self._draw_status(display)
        self._recipe_dialog.draw(display)
        display.show()

        if result is True:
            self._recipe_dialog = None
            price = self.recipe_price_cents / 100
            self.last_result = self._simulate_day(self.recipe_lpg, self.recipe_spg, price)
            self.last_price = price
            if self.last_result["revenue"] > 0:
                self.buzzer.beep(900, 60)
            else:
                self.buzzer.beep(250, 150)
            self.state = "day_result"
        elif result is False:
            self._recipe_dialog = None
            self.recipe_index = RECIPE_LPG
            self.recipe_step = None
            self.state = "recipe"
        return None

    def _update_day_result(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT
        if buttons.pressed("A"):
            self.state = "end_of_day"
            return None

        r = self.last_result
        display.fill(cfg.COLOR_BG)
        self._draw_status(display)
        display.text("Sales Report", 12, 66, cfg.COLOR_CYAN)
        bar = ProgressBar(12, 100, cfg.SCREEN_W - 24, 12)
        bar.draw(display, r["sold"], max(r["customers"], 1), label="Glasses sold")
        display.text(f"{r['sold']} sold", 12, 116, cfg.COLOR_GREEN)
        display.text(f"Revenue: ${r['revenue']:.2f}", 12, 132, cfg.COLOR_GREEN)
        label, color, _ = rep_tier(self.reputation)
        display.text(f"Reputation: {label} ({self.reputation:.0f})", 12, 148, color)
        if r["missed"] > 0:
            display.text(f"Missed {r['missed']} sale(s) - ran out!", 12, 166, cfg.COLOR_RED)
        self._footer(display, "A Continue")
        display.show()
        return None

    def _resolve_end_of_day(self):
        msgs = []
        if self.lemons > 0:
            spoiled = random.randint(0, min(3, self.lemons))
            if spoiled:
                self.lemons -= spoiled
                msgs.append(f"{spoiled} lemon(s) spoiled overnight.")
        if self.signs > 0:
            self.signs = 0
            msgs.append("Signs wore out overnight.")

        self.history.append({
            "day": self.day, "cash": round(self.cash, 2),
            "sold": self.last_result["sold"], "revenue": self.last_result["revenue"],
        })

        if self.last_result["revenue"] == 0:
            self.zero_revenue_streak += 1
        else:
            self.zero_revenue_streak = 0

        prev_season = self.season
        self.day += 1
        new_season = get_season(self.day) if self.day <= self.WIN_DAYS else prev_season
        season_changed = new_season.name != prev_season.name

        reason = None
        if self.cash >= self.WIN_CASH:
            reason = "win_cash"
        elif self.day - 1 >= self.WIN_DAYS:
            reason = "win_days"
        else:
            no_supplies = self.glasses == 0 and self.lemons == 0 and self.sugar == 0
            min_restock = round(3 * self.prices.lemons + 3 * self.prices.glasses
                                + self.prices.sugar, 3)
            if self.cash < self.BROKE_THRESHOLD and no_supplies:
                reason = "bankrupt"
            elif no_supplies and self.cash < min_restock:
                reason = "cant_restock"
            elif self.zero_revenue_streak >= 3:
                reason = "no_sales"

        return msgs, season_changed, new_season, reason

    def _update_end_of_day(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT

        if self._eod_data is None:
            msgs, season_changed, new_season, reason = self._resolve_end_of_day()
            self._eod_data = (msgs, season_changed, new_season, reason)

        msgs, season_changed, new_season, reason = self._eod_data

        if buttons.pressed("A"):
            self._eod_data = None
            if reason:
                self.game_over_reason = reason
                if reason.startswith("win"):
                    self.buzzer.beep(1000, 200)
                else:
                    self.buzzer.beep(200, 250)
                self.state = "game_over"
            else:
                self.state = "day_start"
                self._begin_day()
            return None

        display.fill(cfg.COLOR_BG)
        display.text(f"End of Day {self.day - 1}", 12, 14, cfg.COLOR_WHITE)
        display.hline(12, 28, cfg.SCREEN_W - 24, cfg.COLOR_DARK_GRAY)
        display.text(f"Cash: ${self.cash:.2f}", 12, 38, cfg.COLOR_GREEN)
        display.text(f"Sold: {self.last_result['sold']} glasses", 12, 52, cfg.COLOR_CYAN)
        y = 70
        for m in msgs:
            display.text("- " + m, 12, y, cfg.COLOR_ORANGE)
            y += 14
        if season_changed:
            display.text(f"Season change: {new_season.name}", 12, y + 4, new_season.color)
            y = draw_wrapped(display, new_season.description, 12, y + 18, 26, cfg.COLOR_WHITE)
        self._footer(display, "A Continue")
        display.show()
        return None

    REASON_TEXT = {
        "win_cash": ("YOU WIN!", cfg.COLOR_YELLOW, "You reached ${:.0f}!"),
        "win_days": ("YOU WIN!", cfg.COLOR_YELLOW, "Survived the full {} days!"),
        "bankrupt": ("BANKRUPT", cfg.COLOR_RED, "Out of cash and supplies."),
        "cant_restock": ("OUT OF BUSINESS", cfg.COLOR_RED, "Can't afford to restock."),
        "no_sales": ("ABANDONED", cfg.COLOR_RED, "3 days with no sales."),
    }

    def _update_game_over(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT
        if buttons.pressed("A"):
            self.on_enter(display, buttons)
            return None
        if buttons.pressed("B"):
            return EXIT

        title, color, detail_fmt = self.REASON_TEXT.get(
            self.game_over_reason, ("GAME OVER", cfg.COLOR_RED, ""))
        try:
            detail = detail_fmt.format(self.WIN_CASH) if "cash" in self.game_over_reason \
                else detail_fmt.format(self.WIN_DAYS) if "days" in self.game_over_reason \
                else detail_fmt
        except Exception:
            detail = detail_fmt

        display.fill(cfg.COLOR_BG)
        display.text(title, 16, 12, color)
        display.text(detail, 16, 26, cfg.COLOR_WHITE)
        display.text(f"Days played: {self.day - 1}", 16, 44, cfg.COLOR_WHITE)
        display.text(f"Final cash: ${self.cash:.2f}", 16, 58, cfg.COLOR_GREEN)
        display.text(f"Total sold: {self.total_sold} glasses", 16, 72, cfg.COLOR_CYAN)

        display.text("Revenue history:", 16, 92, cfg.COLOR_GRAY)
        recent = self.history[-6:]
        max_rev = max((h["revenue"] for h in recent), default=0.01) or 0.01
        y = 106
        for h in recent:
            bar_w = int((h["revenue"] / max_rev) * 120)
            display.text(f"D{h['day']}", 16, y, cfg.COLOR_DARK_GRAY)
            display.fill_rect(46, y, max(bar_w, 1), 8, cfg.COLOR_GREEN)
            display.text(f"${h['revenue']:.2f}", 172, y, cfg.COLOR_DARK_GRAY)
            y += 14

        self._footer(display, "A Play again   B Menu")
        display.show()
        return None

    def update(self, display, buttons, dt_ms):
        if self.state == "intro":
            return self._update_intro(display, buttons)
        if self.state == "day_start":
            return self._update_day_start(display, buttons)
        if self.state == "buying":
            return self._update_buying(display, buttons)
        if self.state == "buy_confirm":
            return self._update_buy_confirm(display, buttons)
        if self.state == "recipe":
            return self._update_recipe(display, buttons)
        if self.state == "recipe_confirm":
            return self._update_recipe_confirm(display, buttons)
        if self.state == "day_result":
            return self._update_day_result(display, buttons)
        if self.state == "end_of_day":
            return self._update_end_of_day(display, buttons)
        if self.state == "game_over":
            return self._update_game_over(display, buttons)
        return EXIT
