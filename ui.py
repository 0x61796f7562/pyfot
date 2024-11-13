from datetime import datetime
import urwid
from api import get_lineups, get_matches_grouped_by_tournament, get_substitution_incidents
from monitor import monitor_player_substitution
from data import Player, Match
from app_state import app_state

palette = [
          ("title", "bold,white", "dark gray"), 
          ("subtitle", "bold", ""),
          ("subtitle1", "bold", "dark gray"),
          ("not_selected", "white", "black"),
          ("selected", "black", "white"),
          ("light_bg", "black", "light gray"),
          ("warning", "dark red", ""),
          ("footer", "black", "light gray")
]

class AppContainer(urwid.WidgetPlaceholder):
    window_count = 0
    monitors_list_open = False
    def __init__(self):
        super(urwid.WidgetPlaceholder, self).__init__(urwid.SolidFill(" "))
        self.open(self.create_matches_list_window(), 90, 100)

    
    def open(self, content, width, height):
        self.original_widget = self._create_window(content, self.original_widget, width, height)
        self.window_count += 1

    def close(self):
        if self.window_count != 1:
            self.original_widget = self.original_widget[0]
            self.window_count -= 1
            if self.monitors_list_open:
                self.monitors_list_open = False


    def keypress(self, size, key):
        if key == "esc":
            self.close()
        elif key in ("m", "M"):
            if not self.monitors_list_open:
                self.open(self.create_monitors_list(), 70, 100)
                self.monitors_list_open = True
        else:
            return super(AppContainer, self).keypress(size, key)


    def _create_window(self, new_content, old_content, width, height):
        return urwid.Overlay(urwid.LineBox(new_content), old_content, align="center", valign="middle", width=width, height=height)


    def create_matches_list_window(self):
        header = create_title("Matches")
        body = urwid.Filler(urwid.Text("No Matches Available!", align="center"))
        items = []
        today_date = str(datetime.today().date())
        match_status_text = {
            "inprogress": "In Progress",
            "finished": "Finished"
        }
        matches_by_tournament_list = get_matches_grouped_by_tournament(today_date)
        if matches_by_tournament_list:
            for matches_by_tournament in matches_by_tournament_list:
                tournament_name = create_subtitle(matches_by_tournament.tournamentName)
                items.append(tournament_name)
                for match in matches_by_tournament.matches:
                    if match.status in ("inprogress", "finished"):
                        formated_match_data = f'[{match.time}][{match_status_text[match.status]}] {match.homeTeam.name} {match.homeTeam.score} - {match.awayTeam.score} {match.awayTeam.name}'
                    else:
                        formated_match_data = f'[{match.time}] {match.homeTeam.name} vs {match.awayTeam.name}'
                    match_btn = CustomButton(formated_match_data, align="center")
                    def handle_click(_, match):
                        self.open(self.create_lineups_list_window(match), 60, 80)
                    urwid.connect_signal(match_btn, "click", handle_click, user_arg=match)
                    items.append(match_btn)
            flistb = FilterableListBox(self, items)
            body = flistb

        app_state["monitor"]["status_widget"] = urwid.Text(f'[Active Monitors: {app_state["monitor"]["monitors_count"]}]')
        status_footer = urwid.AttrMap(
            urwid.Filler(
                urwid.Padding(
                    app_state["monitor"]["status_widget"]
                )
            ), 
        "footer")

        frame = urwid.Frame(header=header, body=body, footer=status_footer)
        return frame


    def create_confirmation_window(self, message, btn):
        close_btn = urwid.Button("Close")
        urwid.connect_signal(
            close_btn, 
            "click", 
            lambda _: self.close()
        )
        return urwid.BoxAdapter(
            urwid.AttrMap(
                urwid.Filler(
                    urwid.Padding(
                        urwid.Pile([
                            urwid.Text(message),
                            urwid.Divider(" "),
                            urwid.Columns(
                                [
                                    urwid.AttrMap(btn, None, "not_selected"),
                                    urwid.AttrMap(close_btn, None, "not_selected")
                                ],
                                dividechars=2
                            )
                        ]),
                        left=2,
                        right=2
                    ),
                ), 
                "light_bg"
            ),
            height=6
        )




    def create_start_monitor_window(self, player: Player, match_id: int):
        start_btn = urwid.Button("Start")
        def handle_click_start_btn(_):
            if not player.monitored:
                monitor_player_substitution(match_id, player)
                player.monitored = True

        urwid.connect_signal(
            start_btn, 
            "click", 
            handle_click_start_btn     
        )
        message = f'Start Substitution Monitoring For {player.name}'
        return self.create_confirmation_window(message, start_btn)


    def create_monitors_list(self):
        header = urwid.Pile([create_title("Monitors"), urwid.Divider(" ")])
        body = urwid.Filler(urwid.Text("No Active Monitors!", align="center"))
        items = []
        flistb = FilterableListBox(self, items, False)
        monitors_info_list = app_state["monitor"]["monitors_info_list"]
        if monitors_info_list:
            for index, mi in enumerate(monitors_info_list):
                player_name = mi["player"].name
                cancel_event = mi["cancel_event"]
                task = app_state["monitor"]["tasks"][index]
                if not task.done() and not task.cancelled():
                    def cancel_btn_event_handler(btn, args):
                        if not args[0].is_set():
                            args[0].set()
                            btn.set_text("Stopping")
                    stop_btn = CustomButton(
                        label="Stopping" if cancel_event.is_set() else "Stop", 
                        align="center"
                    )
                    urwid.connect_signal(stop_btn, "click", cancel_btn_event_handler, user_arg=(cancel_event, task))
                    item = urwid.Padding(urwid.Columns([
                        (
                            "weight",
                            85, 
                            urwid.Text(f'Monitor For {player_name}')
                        ),
                        (
                            "weight",
                            15,
                            urwid.AttrMap(
                                stop_btn, 
                            None, "selected")
                        )
                    ]), left=1, right=1)
                    items.append(item)
            if items:
                flistb.body = items
                body = flistb
        
        frame = urwid.Frame(header=header, body=body)
        return frame



    def format_lineup(self, lineup: list[Player], match_id: int):
        subs_incidents = get_substitution_incidents(match_id)
        formated_lineups = []
        ball_unicode = "\u26bd"
        in_out_arrow = {
            "in": "\u2191",
            "out": "\u2193"
        }
        # Starting 11
        starting = [p for p in lineup if not p.substitute]
        formated_lineups.append(create_subtitle1("Starting 11"))
        for player in starting:
            player_subs_incident = player.get_player_subs_incident(
                subs_incidents if subs_incidents else []
            )
            formated_player_data = [
                f'{player.jerseyNumber} {player.name}',
                f'{" ["+str(player.goals)+ball_unicode+"]" if player.goals else ""}', 
                [" [",("warning", str(player.ownGoals)+ball_unicode), "]"] if player.ownGoals else "", 
                f' [{in_out_arrow[player_subs_incident.subsIncidentType]}{player_subs_incident.minute}\']' if player_subs_incident else "",
            ]
            player_btn = CustomButton(formated_player_data, align="center") 
            def handle_click(_, player):
                self.open(self.create_start_monitor_window(player, match_id), 40, "pack") 
            urwid.connect_signal(player_btn, "click", handle_click, user_arg=player)
            formated_lineups.append(player_btn)
        # Substitutions
        subs = [p for p in lineup if p.substitute]
        formated_lineups.append(create_subtitle1("Substitutions"))
        for player in subs:
            player_subs_incident = player.get_player_subs_incident(
                subs_incidents if subs_incidents else []
            )
            formated_player_data = [
                f'{player.jerseyNumber} {player.name}',
                f'{" ["+str(player.goals)+ball_unicode+"]" if player.goals else ""}', 
                [" [",("warning", str(player.ownGoals)+ball_unicode), "]"] if player.ownGoals else "", 
                f' [{in_out_arrow[player_subs_incident.subsIncidentType]}{player_subs_incident.minute}\']' if player_subs_incident else "",
            ]
            player_btn = CustomButton(formated_player_data, align="center") 
            def handle_click(_, player):
                self.open(self.create_start_monitor_window(player, match_id), 40, "pack") 
            urwid.connect_signal(player_btn, "click", handle_click, user_arg=player)
            formated_lineups.append(player_btn)

        return formated_lineups


    def create_lineups_list_window(self, match: Match):
        lineups = get_lineups(match.id)
        title = create_title("Lineups")    
        header = urwid.Pile([title, urwid.Divider(" ")])
        body = urwid.Filler(urwid.Text("No Lineups Available!", align="center"))
        if lineups:
            home_team_name = create_subtitle(f'Home Team: {match.homeTeam.name}')
            items = []
            items.append(home_team_name)
            items = [*items, *self.format_lineup(lineups.homeLineup, match.id)]
            away_team_name = create_subtitle(f'Away Team: {match.awayTeam.name}')
            items.append(away_team_name)
            items = [*items, *self.format_lineup(lineups.awayLineup, match.id)]
            body = FilterableListBox(self, items)
        frame = urwid.Frame(header=header, body=body)
        return frame






class CustomButton(urwid.Button):
    def __init__(self, label, *args, **kwargs):
        super().__init__(label, *args, **kwargs)
        self.si = urwid.SelectableIcon(label, *args, **kwargs, cursor_position=1000)
        self._w = urwid.AttrMap(self.si, None, "selected")
        self.text = self._w.original_widget.text
    
    def set_text(self, label: str) -> None:
        self.si.set_text(label)



class FilterableListBox(urwid.ListBox):
    app_container: AppContainer
    def __init__(self, app_conainer_ref, items, filterable=True):
        self.app_container = app_conainer_ref
        self.items = items
        self.filterable = filterable
        self.filter_text = ""
        self.filtered_items = [*self.items]
        self.list_walker = urwid.SimpleFocusListWalker(self.filtered_items)
        super(FilterableListBox, self).__init__(self.list_walker)


    def keypress(self, size, key):
        if key in ("f", "F"):
            if self.filterable:
                self.app_container.open(self._create_filter_window(), 40, "pack")
        else:
            return super(FilterableListBox, self).keypress(size, key)

    def _create_filter_window(self):
        filter_edit = urwid.LineBox(urwid.Edit(edit_text=self.filter_text), "Filter", title_align="left")
        urwid.connect_signal(filter_edit.original_widget, "change", lambda _, value: self.filter(value))
        reset_btn = urwid.Button("Reset")
        urwid.connect_signal(reset_btn, "click", lambda _: self.reset_filter(filter_edit.original_widget))
        close_btn = urwid.Button("Close")
        urwid.connect_signal(close_btn, "click", lambda _: self.app_container.close())

        return urwid.BoxAdapter(
            urwid.AttrMap(
                urwid.Filler(
                    urwid.Padding(
                        urwid.Pile(
                            [
                                filter_edit, 
                                urwid.Columns(
                                    [
                                        urwid.AttrMap(reset_btn, None, "not_selected"),
                                        urwid.AttrMap(close_btn, None, "not_selected"),
                                    ], 
                                2)
                            ]
                        ),
                        left=2,
                        right=2
                    )
                ), "light_bg"

        ), height=6)
    
    def filter(self, filter_text):
        def get_text(w):
            if hasattr(w, "text"):
                return w.text
            else:
                return get_text(w.original_widget)

        self.filter_text = filter_text

        self.filtered_items = [item for item in self.items if filter_text.lower() in get_text(item).lower()]
        self.body = self.filtered_items
        self.list_walker.focus = 0
        
        # for i, item in enumerate(self.items):
        #     if filter_text.lower() in get_text(item).lower():
        #         self.set_focus(i)

    def reset_filter(self, edit):
        edit.edit_text = ""


def create_title(text: str):
    return urwid.AttrMap(urwid.Filler(urwid.Text(text, align="center"), top=1, bottom=1), "title")

def create_subtitle(text: str):
    return urwid.LineBox(urwid.AttrMap(urwid.Filler(urwid.Text(text, align="center")), "subtitle"))

def create_subtitle1(text: str):
    return urwid.AttrMap(urwid.Filler(urwid.Text(text, align="center"), top=1, bottom=1), "subtitle")







