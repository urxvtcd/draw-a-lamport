import sys

import drawsvg as draw


TICK_WIDTH = 30
ACTOR_HEIGHT = 80

TICK_SEND_OFFSET = -0
TICK_RECEIVE_OFFSET = 0

ACTOR_MARGIN_X = 20
ACTOR_MARGIN_Y = 25

MSG_MARGIN = 20

ARROW_HEADROOM = 2
BAD_ARROW_HEADROOM_X = 5
BAD_ARROW_HEADROOM_Y = 15

MESSAGE_LINE_COLOR = "black"
ACTOR_LINE_COLOR = "gray"


def make_arrow(color):
    arrow = draw.Marker(-1, -1, 1, 1, scale=3, orient='auto')
    arrow.append(draw.Lines(-1, 0.5, -1, -0.5, 0.3, 0, fill=color, close=True))
    return arrow


def make_bad_arrow():
    arrow = draw.Marker(-3, -3, 3, 3, scale=1, orient='auto')
    arrow.append(draw.Line(-2, -2, 2, 2, stroke="red", stroke_width=1))
    arrow.append(draw.Line(-2, 2, 2, -2, stroke="red", stroke_width=1))
    return arrow


MSG_ARROW = make_arrow(MESSAGE_LINE_COLOR)
BAD_ARROW = make_bad_arrow()


def label(line, text, anchor=None):
    if anchor == "start":
        alignment = {"start_offset": 5}
    elif anchor == "end":
        alignment = {"text_anchor": "end"}
    elif anchor == "middle":
        alignment = {"text_anchor": "middle"}
    else:
        alignment = {"start_offset": 0}

    return draw.Text(
        text,
        font_size=8,
        font_family="Verdana",
        path=line,
        line_offset=-0.6,
        **alignment,
    )


def draw_actor_lines(ticks, actors):
    lines = []

    for index, actor in enumerate(actors):
        line = draw.Line(
            ACTOR_MARGIN_X,
            ACTOR_MARGIN_Y + index * ACTOR_HEIGHT,
            ACTOR_MARGIN_X + (ticks -1) * TICK_WIDTH + MSG_MARGIN * 2,
            ACTOR_MARGIN_Y + index * ACTOR_HEIGHT,
            stroke=ACTOR_LINE_COLOR,
        )
        lines.append(line)
        lines.append(label(line, actor))

    return lines


def draw_msg_line(source_tick, source_actor_index, target_tick, target_actor_index, msg_text):
    assert source_actor_index != target_actor_index, "Actor can't send a message to itself"

    if msg_text.startswith("<"):
        anchor = "start"
        msg_text = msg_text[1:]
    elif msg_text.startswith(">"):
        anchor = "end"
        msg_text = msg_text[1:]
    else:
        anchor = "middle"

    up = source_actor_index > target_actor_index
    headroom = ARROW_HEADROOM if up else - ARROW_HEADROOM
    line = draw.Line(
        ACTOR_MARGIN_X + MSG_MARGIN + source_tick * TICK_WIDTH + TICK_SEND_OFFSET,
        ACTOR_MARGIN_Y + source_actor_index * ACTOR_HEIGHT,
        ACTOR_MARGIN_X + MSG_MARGIN + target_tick * TICK_WIDTH + TICK_RECEIVE_OFFSET,
        ACTOR_MARGIN_Y + target_actor_index * ACTOR_HEIGHT + headroom,
        stroke=MESSAGE_LINE_COLOR,
        stroke_width=2,
        marker_end=MSG_ARROW,
    )
    return [line, label(line, msg_text, anchor)]


def draw_bad_msg_line(source_tick, source_actor_index, target_tick, target_actor_index, msg_text):
    assert source_actor_index != target_actor_index, "Actor can't send a message to itself"

    if msg_text.startswith("<"):
        anchor = "start"
        msg_text = msg_text[1:]
    elif msg_text.startswith(">"):
        anchor = "end"
        msg_text = msg_text[1:]
    else:
        anchor = "middle"

    up = source_actor_index > target_actor_index
    headroom_y = BAD_ARROW_HEADROOM_Y if up else - BAD_ARROW_HEADROOM_Y
    line = draw.Line(
        ACTOR_MARGIN_X + MSG_MARGIN + source_tick * TICK_WIDTH + TICK_SEND_OFFSET,
        ACTOR_MARGIN_Y + source_actor_index * ACTOR_HEIGHT,
        ACTOR_MARGIN_X + MSG_MARGIN + target_tick * TICK_WIDTH + TICK_RECEIVE_OFFSET - BAD_ARROW_HEADROOM_X,
        ACTOR_MARGIN_Y + target_actor_index * ACTOR_HEIGHT + headroom_y,
        stroke=MESSAGE_LINE_COLOR,
        stroke_width=2,
        marker_end=BAD_ARROW,
    )
    return [line, label(line, msg_text, anchor)]


def read_diagram(source):
    actors = []
    events = []
    first = True

    for line in source.splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue

        if line == "":
            first = False
        elif first:
            actors.append(line)
        else:
            events.append(line)

    return actors, events


def draw_marker(op, actor, tick):
    marker = op[:-1]
    if not marker:
        return None

    if op[-1] == "s":
        x = ACTOR_MARGIN_X + MSG_MARGIN + tick * TICK_WIDTH + TICK_SEND_OFFSET -10
        y = ACTOR_MARGIN_Y + actor * ACTOR_HEIGHT + 10
        return draw.Text(
            text=marker,
            x=x,
            y=y,
            font_size=8,
            font_family="Verdana",
            line_offset=-1,
        )
    else:
        x = ACTOR_MARGIN_X + MSG_MARGIN + tick * TICK_WIDTH + TICK_SEND_OFFSET +3
        y = ACTOR_MARGIN_Y + actor * ACTOR_HEIGHT - 5
        return draw.Text(
            text=marker,
            x=x,
            y=y,
            font_size=8,
            font_family="Verdana",
            line_offset=-1,
        )



def draw_messages(actors, ticks):
    messages = {}
    msg_lines = []

    for t, event in enumerate(ticks):
        [op, actor, msg] = event.split(maxsplit=2)

        if marker := draw_marker(op, actors.index(actor), t):
            msg_lines.append(marker)

        if op.endswith("s"):
            split = msg.split(":", maxsplit=1)
            messages[split[0].strip("<>")] = (actors.index(actor), t, split[-1].strip())
        elif op.endswith("r"):
            target_actor = actors.index(actor)
            (source_actor, source_tick, msg_text) = messages.pop(msg)
            msg_lines.extend(draw_msg_line(source_tick, source_actor, t, target_actor, msg_text))
        elif op.endswith("x"):
            target_actor = actors.index(actor)
            (source_actor, source_tick, msg_text) = messages.pop(msg)
            msg_lines.extend(draw_bad_msg_line(source_tick, source_actor, t, target_actor, msg_text))
        else:
            raise Exception(f"Invalid event '{event}'")

    return msg_lines


def draw_diagram(actors, ticks, output_filename):
    d = draw.Drawing(
        TICK_WIDTH * (len(ticks) - 1) + 2 * (ACTOR_MARGIN_X + MSG_MARGIN),
        ACTOR_HEIGHT * (len(actors) - 1) + 2 * ACTOR_MARGIN_Y,
    )
    d.set_pixel_scale(2)

    for line in draw_actor_lines(len(ticks), actors):
        d.append(line)

    for line in draw_messages(actors, ticks):
        d.append(line)

    d.save_svg(output_filename)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        source_filename = sys.argv[1]
        target_filename = sys.argv[2]

        with open(source_filename) as source:
            actors, events = read_diagram(source.read())
            draw_diagram(actors, events, target_filename)
    else:
        print("Usage:")
        print("        python main.py <source-filename> <target-filename>")
