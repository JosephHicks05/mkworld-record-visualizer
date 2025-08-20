from matplotlib.lines import Line2D
import requests
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
from matplotlib.typing import ColorType
from urllib.parse import quote_plus
from urllib.parse import unquote_plus
from random import random
from random import choice as rand_choice
from typing import Literal
from typing import TextIO
from collections import Counter


BASE_URL: str = "https://mkwrs.com/mkworld/"
RECORD_BASE_URL: str = f"{BASE_URL}display.php?track="
RECORD_MEMO_FILE_PATH: str = "C:\\Users\\justj\\OneDrive\\CS\\personal\\web_stuff\\mkworld_datavis\\record_memo.txt"
TODAYS_DATE: date = date.today()
RELEASE_DATE: date = date(2025, 6, 5)

class Record:
    def __init__(self, time_seconds: float, date_set: date, player: str, country: str):
        self.time_seconds: float = time_seconds
        self.date_set: date = date_set
        self.player: str = player
        self.country: str = country

    def __str__(self) -> str:
        return f"record by {self.player} from {self.country} on {self.date_set} in {self.time_seconds} seconds"


class Track:
    def __init__(self, name: str, records: list[Record]):
        self.name = name
        self.records = records


    def get_record_at_date(self, record_date: date) -> Record:
        for i in range(1, len(self.records)):
            if self.records[i].date_set > record_date:
                return self.records[i - 1]
            
        return self.records[-1]


tracks: list[Track] = []


def parse_track_names(track_names_html: str) -> list[str]:
    track_names: list[str] = []
    search_index: int = track_names_html.find("<a")

    while search_index != -1:
        name_start_index: int = track_names_html.find(">", search_index) + 1
        name_end_index: int = track_names_html.find("</a>", search_index)
        track_names.append(track_names_html[name_start_index : name_end_index])
        search_index = track_names_html.find("<a", search_index + 1)

    return track_names


def get_track_names() -> list[str]:
    track_names_html: str = requests.get(BASE_URL, ).text
    search_index: int = track_names_html.index("<u>WR History</u>")
    end_search_index: int = track_names_html.index("<u>Other</u>")

    track_names_html = track_names_html[search_index:end_search_index]
    return parse_track_names(track_names_html)
    


def get_track_html(track_name: str) -> str:
    track_url: str = f"{RECORD_BASE_URL}{quote_plus(track_name)}"
    return requests.get(track_url).text


def get_records_raw_data(track_html: str) -> list[str]:
    searching_index: int = track_html.find("<h2>History</h2>")
    records_raw_data: list[str] = []

    while track_html.find("</tr>", searching_index + 1) != -1:
        end_record_data_index: int = track_html.find("</tr>", searching_index + 1)
        record_raw_data: str = track_html[searching_index : end_record_data_index]

        if len(record_raw_data.split("\n")) > 6: # only add if entry represents a record
            records_raw_data.append(track_html[searching_index : end_record_data_index])

        searching_index = end_record_data_index

    return records_raw_data[2:] # remove table header and prerelease records


def parse_time_line(time_line: str) -> float:
    time_text: str = time_line[time_line.index("\'") - 1 : time_line.index("\'") + 7]

    minutes: int = int(time_text[0])
    seconds: int = int(time_text[2:4])
    miliseconds: int = int(time_text[5:8])
    return (minutes * 60) + seconds + (miliseconds / 1000)


def parse_date_line(date_line: str) -> date:
    if  "rowspan=2" in date_line:
        return datetime.strptime(date_line[26:36], "%Y-%m-%d").date()
    
    else:
        return datetime.strptime(date_line[16:26], "%Y-%m-%d").date()
    

def parse_player_line(player_line: str) -> str:
    if "rowspan=2" in player_line:
        return player_line[56:player_line.index("\"", 56)]
    
    else:
        return player_line[46:player_line.index("\"", 46)]
    

def parse_country_line(country_line: str) -> str:
    if "rowspan=2" in country_line:
        return country_line[46:country_line.index("\"", 46)]
    
    else:
        return country_line[36:country_line.index("\"", 36)]


def parse_single_record_data(data: str) -> Record:
    data_lines: list[str] = data.split("\n")

    date_line: str = data_lines[2]
    time_line: str = data_lines[3]
    player_line: str = data_lines[4]
    country_line: str = data_lines[5]

    record_date: date = parse_date_line(date_line)
    record_time: float = parse_time_line(time_line)
    record_player: str = parse_player_line(player_line)
    record_country: str = parse_country_line(country_line)

    return Record(record_time, record_date, record_player, record_country)


def remove_same_day_records(records: list[Record]) -> list[Record]:
    non_duplicate_records: list[Record] = []
    last_date: date | None = None # type: ignore

    for record in records:
        if record.date_set != last_date:
            non_duplicate_records.append(record)
        else:
            non_duplicate_records[-1] = record
        
        last_date: date = record.date_set

    return non_duplicate_records


def parse_track_record_data(data: list[str]) -> list[Record]:
    records: list[Record] = []

    for record_data in data:
        records.append(parse_single_record_data(record_data))

    records = remove_same_day_records(records)
    return records


def get_color(taken: set[ColorType]) -> ColorType:
    RED: ColorType = (1, 0, 0)
    GREEN: ColorType = (0, 1, 0)
    BLUE: ColorType = (0, 0, 1)
    BLACK: ColorType = (0, 0, 0)
    PURPLE: ColorType = (0.5, 0, 0.5)
    DARK_GREEN: ColorType = (0, 0.5, 0)
    ORANGE: ColorType = (1, 0.5, 0)
    BROWN: ColorType = (0.6, 0.3, 0.1)
    MAGENTA: ColorType = (1, 0, 1)
    CYAN: ColorType = (0, 1, 1)
    GRAY: ColorType = (.3, .3, .3)

    available_colors: set[ColorType] = {RED, GREEN, BLUE, BLACK, PURPLE, DARK_GREEN,
                                        ORANGE, BROWN, MAGENTA, CYAN, GRAY} - taken

    if available_colors == set():
        return (random(), random(), random())
    else:
        return rand_choice(list(available_colors))



def color_plot_lines(lines: list[Line2D], records: list[Record]) -> dict[str, ColorType]:
    player_color_mapping: dict[str, ColorType] = {}

    for record, line in zip(records, lines):
        if record.player not in player_color_mapping:
            player_color_mapping[record.player] = get_color(set(player_color_mapping.values()))
            line.set_label(f"{unquote_plus(record.player)} ({record.country})")
        
        line.set_color(player_color_mapping[record.player])

    return player_color_mapping


def add_plot_lines(records: list[Record]) -> list[Line2D]:
    lines: list[Line2D] = []

    records = records[:] + [Record(records[-1].time_seconds, TODAYS_DATE, "", "")]
    for index, record in enumerate(records[:-1]):
        record_date_jump: list[date] = [record.date_set, records[index + 1].date_set]
        record_time_jump: list[float] = [record.time_seconds, records[index + 1].time_seconds]
        lines.append(plt.step(record_date_jump, record_time_jump, where='post')[0]) # type: ignore

    return lines


def generate_record_plot(track: Track) -> None:
    records: list[Record] = track.records

    fig = plt.subplots()[0]
    fig.canvas.manager.set_window_title(f"MKWorld World Record Progression: {track.name}") # type: ignore

    lines: list[Line2D] = add_plot_lines(records)
    player_color_mapping: dict[str, ColorType] = color_plot_lines(lines, records)

    plt.rcParams['font.family'] = 'Yu Gothic'
    plt.legend()
    plt.xlabel("Date")
    plt.ylabel("Record Time (sec)")
    plt.title(f"{track.name} World Record Progression")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(True)
    plt.show()


def get_record_day_map(records: list[Record], type: Literal["player", "country"]) -> Counter[str]:
    record_day_map: dict[str, int] = {}

    records = records[:] + [Record(0, TODAYS_DATE, "", "")]
    for index, record in enumerate(records[:-1]):
        map_entry: str = record.player if type == "player" else record.country

        record_duration_days = (records[index + 1].date_set - record.date_set).days
        
        if map_entry not in record_day_map:
            record_day_map[map_entry] = 0

        record_day_map[map_entry] += record_duration_days

    return Counter(record_day_map)


def record_memo_current() -> bool:
    try:
        reader: TextIO = open(RECORD_MEMO_FILE_PATH, "r")
    except FileNotFoundError:
        return False
    file_header: str = reader.readline()
    reader.close()
    if file_header == "" or datetime.strptime(file_header.split(" ")[0], "%Y-%m-%d").date() != TODAYS_DATE:
        return False
    
    return True


def parse_track_data(track_data: str) -> Track:
    track_data_lines: list[str] = track_data.split("\n")
    track_name: str = track_data_lines[0]
    track_records: list[Record] = []

    for record_data in track_data_lines[1:]:
        record_data_list: list[str] = record_data.split(",")
        record_time: float = float(record_data_list[0])
        record_date: date = datetime.strptime(record_data_list[1], "%Y-%m-%d").date()
        record_player: str = record_data_list[2]
        record_country: str = record_data_list[3]
        track_records.append(Record(record_time, record_date, record_player, record_country))

    return Track(track_name, track_records)


def load_record_memo() -> None:
    reader: TextIO = open(RECORD_MEMO_FILE_PATH, "r")

    tracks_data: list[str] = reader.read().split("\n\n")[1:]
    reader.close()
    
    for track_data in tracks_data:
        tracks.append(parse_track_data(track_data))


def write_track_data(track: Track, writer: TextIO) -> None:
    writer.write(f"{track.name}\n")

    for record in track.records:
        writer.write(f"{record.time_seconds},{record.date_set},{record.player},{record.country}")

        if track.records[-1] != record:
            writer.write("\n")


def update_record_memo() -> None:
    writer: TextIO = open(RECORD_MEMO_FILE_PATH, "w")
    writer.write(f"{TODAYS_DATE} last updated\n\n")

    for track in tracks:
        write_track_data(track, writer)

        if tracks[-1] != track:
            writer.write("\n\n")

    writer.close()


def fill_track_data() -> None:
    if tracks != []:
        return
    
    if record_memo_current():
        load_record_memo()
        return
    
    track_names: list[str] = get_track_names()

    for track_name in track_names:
        track_html = get_track_html(track_name)

        records_raw_data = get_records_raw_data(track_html)

        records = parse_track_record_data(records_raw_data)

        tracks.append(Track(track_name, records))
        print(track_name, "Done")

    update_record_memo()
    print("all tracks done")


def get_all_track_mapping(type: Literal["player", "country"]) -> Counter[str]:
    fill_track_data()

    track_record_maps: list[Counter[str]] = []
    for track in tracks:
        track_record_maps.append(get_record_day_map(track.records, type))

    return sum(track_record_maps, Counter())



def graph_all_tracks() -> None:
    fill_track_data()
    
    for track in tracks:
        generate_record_plot(track)


def get_combined_track() -> Track:
    fill_track_data()

    combined_records: list[Record] = []

    date_surveying: date = RELEASE_DATE

    while date_surveying <= TODAYS_DATE:
        combined_time: float = 0
        for track in tracks:
            combined_time += track.get_record_at_date(date_surveying).time_seconds
        combined_records.append(Record(combined_time, date_surveying, "Community", "World"))

        date_surveying += timedelta(days=1)

    return Track("All Tracks Combined", combined_records)



generate_record_plot(get_combined_track())
