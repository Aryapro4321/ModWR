# ba_meta require api 9

from __future__ import annotations

import re

import babase
import bauiv1 as bui
from babase import Plugin
from bauiv1lib import party


# ============================================================
# GLOBALS
# ============================================================

_original_init = None
_original_popup = None
_original_send = None

_button_installed = False
_popup_patched = False
_send_patched = False

CONFIG_KEY = 'WR_CUSTOM_MESSAGES'
CUSTOM_MESSAGES = {}

ACTION_DELAY = 0.01

_sending_auto = False

# FR:
# False = HUG
# True  = FL
_FR_TOGGLE = False

_WR_BUTTON = None

# آخرین پلیر انتخاب شده از منوی سه نقطه
_LAST_TARGET_CLIENT_ID = None


# ============================================================
# MESSAGE
# ============================================================

def msg(text):

    try:

        bui.screenmessage(
            str(text),
            color=(1.0, 1.0, 0.2)
        )

    except Exception:

        pass


# ============================================================
# LOAD SETTINGS
# ============================================================

def load_settings():

    global CUSTOM_MESSAGES

    try:

        data = babase.app.config.get(
            CONFIG_KEY,
            {}
        )

        if isinstance(data, dict):

            messages = data.get(
                'messages',
                {}
            )

            if isinstance(messages, dict):

                CUSTOM_MESSAGES = {}

                for code, text in messages.items():

                    code = (
                        str(code)
                        .strip()
                        .lower()
                        .lstrip('%')
                    )

                    if code:

                        CUSTOM_MESSAGES[code] = str(text)

    except Exception as exc:

        print(
            'WR9 LOAD ERROR:',
            repr(exc)
        )

        CUSTOM_MESSAGES = {}


# ============================================================
# SAVE SETTINGS
# ============================================================

def save_settings():

    try:

        babase.app.config[
            CONFIG_KEY
        ] = {
            'messages': dict(
                CUSTOM_MESSAGES
            )
        }

        babase.app.config.commit()

        return True

    except Exception as exc:

        print(
            'WR9 SAVE ERROR:',
            repr(exc)
        )

        return False


# ============================================================
# TARGET INFO
# ============================================================

def get_target_info(
    player,
    client_id
):

    name_full = str(
        player.get(
            'name_full',
            ''
        )
    ).strip()

    match = re.match(
        r'^(\d+)\s+(.+)$',
        name_full
    )

    if match:

        return (
            match.group(1),
            match.group(2).strip()
        )

    if client_id is not None:

        return (
            str(client_id),
            str(
                player.get(
                    'name',
                    ''
                )
            ).strip()
        )

    return None, ''


# ============================================================
# FIND PLAYER
#
# هم client_id را می‌گیرد
# هم Player ID داخل name_full را
# ============================================================

def find_player(
    window,
    client_id
):

    roster = getattr(
        window,
        '_roster',
        []
    )

    wanted = str(
        client_id
    ).strip()

    for entry in roster:

        if not isinstance(
            entry,
            dict
        ):

            continue

        entry_client_id = entry.get(
            'client_id'
        )

        players = entry.get(
            'players',
            []
        )

        if not players:

            continue

        player = players[0]

        # ----------------------------------------------------
        # حالت اول:
        # CLIENT ID
        # ----------------------------------------------------

        if str(
            entry_client_id
        ).strip() == wanted:

            return (
                player,
                entry_client_id
            )

        # ----------------------------------------------------
        # حالت دوم:
        # PLAYER ID
        #
        # مثال:
        # 140 PlayerName
        # ----------------------------------------------------

        name_full = str(
            player.get(
                'name_full',
                ''
            )
        ).strip()

        match = re.match(
            r'^(\d+)\s+(.+)$',
            name_full
        )

        if match:

            player_id = match.group(
                1
            )

            if player_id == wanted:

                return (
                    player,
                    entry_client_id
                )

    return None, None


# ============================================================
# BUILD CUSTOM TEXT
# ============================================================

def build_text(
    player,
    client_id,
    code
):

    code = (
        str(code)
        .strip()
        .lower()
        .lstrip('%')
    )

    if code not in CUSTOM_MESSAGES:

        return None

    target_id, name = get_target_info(
        player,
        client_id
    )

    if target_id is None:

        return None

    text = str(
        CUSTOM_MESSAGES[code]
    )

    text = text.replace(
        '{id}',
        str(target_id)
    )

    text = text.replace(
        '{name}',
        str(name)
    )

    return text


# ============================================================
# REAL SEND
# ============================================================

def send_message(
    window,
    text
):

    global _sending_auto

    if window is None:

        return False

    try:

        if _sending_auto:

            return False

        text_field = getattr(
            window,
            '_text_field',
            None
        )

        if text_field is None:

            print(
                'WR9 TEXT FIELD NOT FOUND'
            )

            return False

        if not callable(
            _original_send
        ):

            print(
                'WR9 REAL SEND NOT FOUND'
            )

            return False

        _sending_auto = True

        bui.textwidget(
            edit=text_field,
            text=str(text)
        )

        _original_send(
            window
        )

        print(
            'WR9 REAL SENT:',
            repr(text)
        )

        return True

    except Exception as exc:

        print(
            'WR9 SEND ERROR:',
            repr(exc)
        )

        return False

    finally:

        _sending_auto = False


# ============================================================
# SEND CUSTOM
# ============================================================

def send_custom_for_player(
    window,
    player,
    client_id,
    code
):

    if player is None:

        return False

    text = build_text(
        player,
        client_id,
        code
    )

    if text is None:

        return False

    return send_message(
        window,
        text
    )


# ============================================================
# CU -> HUG
# ============================================================

def custom_cu(
    window,
    player,
    client_id
):

    load_settings()

    # --------------------------------------------------------
    # CU
    # --------------------------------------------------------

    cu_text = build_text(
        player,
        client_id,
        'cu'
    )

    if cu_text is not None:

        if not send_message(
            window,
            cu_text
        ):

            return False

    else:

        msg(
            'NO CUSTOM CU'
        )

        return False

    # --------------------------------------------------------
    # HUG
    # --------------------------------------------------------

    hug_text = build_text(
        player,
        client_id,
        'hug'
    )

    if hug_text is None:

        print(
            'WR9 NO CUSTOM: HUG'
        )

        return True

    babase.apptimer(
        ACTION_DELAY,
        bui.Call(
            send_message,
            window,
            hug_text
        )
    )

    print(
        'WR9 CU -> HUG'
    )

    return True


# ============================================================
# FR -> HUG / FL
# ============================================================

def faster_fr(
    window,
    player,
    client_id
):

    global _FR_TOGGLE

    load_settings()

    # --------------------------------------------------------
    # FR
    # --------------------------------------------------------

    fr_text = build_text(
        player,
        client_id,
        'fr'
    )

    if fr_text is None:

        msg(
            'NO CUSTOM FR'
        )

        return False

    if not send_message(
        window,
        fr_text
    ):

        return False

    # --------------------------------------------------------
    # HUG / FL
    # --------------------------------------------------------

    if _FR_TOGGLE is False:

        next_code = 'hug'

    else:

        next_code = 'fl'

    _FR_TOGGLE = not _FR_TOGGLE

    next_text = build_text(
        player,
        client_id,
        next_code
    )

    if next_text is None:

        print(
            'WR9 NO CUSTOM:',
            next_code
        )

        return True

    babase.apptimer(
        ACTION_DELAY,
        bui.Call(
            send_message,
            window,
            next_text
        )
    )

    print(
        'WR9 FR ->',
        next_code.upper()
    )

    return True


# ============================================================
# INSTALL REAL SEND
#
# MANUAL:
#
# cu
# %cu
# cu 140
# %cu 140
#
# fr
# %fr
# fr 140
#
# custom
# custom 140
#
# ============================================================

def install_send():

    global _original_send
    global _send_patched

    if _send_patched:

        return

    try:

        cls = party.PartyWindow

        original = getattr(
            cls,
            '_send_chat_message',
            None
        )

        if not callable(original):

            print(
                'WR9 REAL SEND NOT FOUND'
            )

            return

        _original_send = original

        # ----------------------------------------------------
        # MANUAL SEND HOOK
        # ----------------------------------------------------

        def manual_send_hook(
            self,
            *args,
            **kwargs
        ):

            global _sending_auto

            # ------------------------------------------------
            # ارسال خودکار مود
            # ------------------------------------------------

            if _sending_auto:

                return _original_send(
                    self,
                    *args,
                    **kwargs
                )

            try:

                text_field = getattr(
                    self,
                    '_text_field',
                    None
                )

                if text_field is None:

                    return _original_send(
                        self,
                        *args,
                        **kwargs
                    )

                # ------------------------------------------------
                # متن دستی
                # ------------------------------------------------

                typed_text = str(
                    bui.textwidget(
                        query=text_field
                    )
                ).strip()

                print(
                    'WR9 MANUAL TEXT:',
                    repr(typed_text)
                )

                if not typed_text:

                    return _original_send(
                        self,
                        *args,
                        **kwargs
                    )

                parts = typed_text.split()

                if not parts:

                    return _original_send(
                        self,
                        *args,
                        **kwargs
                    )

                # ------------------------------------------------
                # CODE
                # ------------------------------------------------

                code = (
                    parts[0]
                    .strip()
                    .lower()
                    .lstrip('%')
                )

                # ------------------------------------------------
                # کد نامعتبر
                # ------------------------------------------------

                if not re.match(
                    r'^[a-zA-Z0-9_]+$',
                    code
                ):

                    return _original_send(
                        self,
                        *args,
                        **kwargs
                    )

                # ------------------------------------------------
                # فقط کدهای مود
                # ------------------------------------------------

                is_special = (
                    code == 'cu'
                    or code == 'fr'
                    or code in CUSTOM_MESSAGES
                )

                if not is_special:

                    return _original_send(
                        self,
                        *args,
                        **kwargs
                    )

                # ------------------------------------------------
                # TARGET
                #
                # اول آخرین بازیکن انتخاب شده
                # ------------------------------------------------

                target_id = (
                    _LAST_TARGET_CLIENT_ID
                )

                # ------------------------------------------------
                # اگر ID بعد از CODE نوشته شده
                #
                # cu 140
                # fr 140
                # hug 140
                # ------------------------------------------------

                if len(parts) >= 2:

                    possible_id = (
                        parts[1]
                        .strip()
                    )

                    if possible_id.isdigit():

                        target_id = (
                            possible_id
                        )

                        print(
                            'WR9 MANUAL PLAYER ID:',
                            target_id
                        )

                # ------------------------------------------------
                # هدف پیدا نشد
                # ------------------------------------------------

                if target_id is None:

                    msg(
                        'SELECT PLAYER FIRST'
                    )

                    return None

                # ------------------------------------------------
                # پیدا کردن پلیر
                #
                # هم Player ID
                # هم Client ID
                # ------------------------------------------------

                player, real_client_id = find_player(
                    self,
                    target_id
                )

                if player is None:

                    msg(
                        'PLAYER ID NOT FOUND: '
                        + str(target_id)
                    )

                    print(
                        'WR9 TARGET NOT FOUND:',
                        target_id
                    )

                    return None

                # ------------------------------------------------
                # CU -> HUG
                # ------------------------------------------------

                if code == 'cu':

                    print(
                        'WR9 MANUAL CU -> HUG:',
                        target_id
                    )

                    custom_cu(
                        self,
                        player,
                        real_client_id
                    )

                    return None

                # ------------------------------------------------
                # FR -> HUG / FL
                # ------------------------------------------------

                if code == 'fr':

                    print(
                        'WR9 MANUAL FR:',
                        target_id
                    )

                    faster_fr(
                        self,
                        player,
                        real_client_id
                    )

                    return None

                # ------------------------------------------------
                # CUSTOM CODE
                # ------------------------------------------------

                print(
                    'WR9 MANUAL CUSTOM:',
                    code,
                    target_id
                )

                send_custom_for_player(
                    self,
                    player,
                    real_client_id,
                    code
                )

                return None

            except Exception as exc:

                print(
                    'WR9 MANUAL SEND ERROR:',
                    repr(exc)
                )

                return _original_send(
                    self,
                    *args,
                    **kwargs
                )

        # ----------------------------------------------------
        # INSTALL HOOK
        # ----------------------------------------------------

        cls._send_chat_message = (
            manual_send_hook
        )

        _send_patched = True

        print(
            'WR9 MANUAL SEND ACTIVE'
        )

    except Exception as exc:

        print(
            'WR9 SEND INSTALL ERROR:',
            repr(exc)
        )


# ============================================================
# POPUP HOOK
# ============================================================

def popup_hook(
    self,
    popup_window,
    choice,
    *args,
    **kwargs
):

    global _LAST_TARGET_CLIENT_ID

    try:

        client_id = getattr(
            self,
            '_popup_party_member_client_id',
            None
        )

        # ----------------------------------------------------
        # ذخیره بازیکن انتخاب شده
        # ----------------------------------------------------

        if client_id is not None:

            _LAST_TARGET_CLIENT_ID = (
                client_id
            )

            print(
                'WR9 TARGET:',
                client_id
            )

        # ----------------------------------------------------
        # منوی اصلی
        # ----------------------------------------------------

        if client_id is None:

            if callable(
                _original_popup
            ):

                return _original_popup(
                    self,
                    popup_window,
                    choice,
                    *args,
                    **kwargs
                )

            return None

        player, real_client_id = find_player(
            self,
            client_id
        )

        code = (
            str(choice)
            .strip()
            .lower()
            .lstrip('%')
        )

        # ----------------------------------------------------
        # CU
        # ----------------------------------------------------

        if code == 'cu':

            if player is not None:

                custom_cu(
                    self,
                    player,
                    real_client_id
                )

            return None

        # ----------------------------------------------------
        # FR
        # ----------------------------------------------------

        if code == 'fr':

            if player is not None:

                faster_fr(
                    self,
                    player,
                    real_client_id
                )

            return None

        # ----------------------------------------------------
        # CUSTOM
        # ----------------------------------------------------

        if code in CUSTOM_MESSAGES:

            if player is not None:

                send_custom_for_player(
                    self,
                    player,
                    real_client_id,
                    code
                )

            return None

        # ----------------------------------------------------
        # ORIGINAL
        # ----------------------------------------------------

        if callable(
            _original_popup
        ):

            return _original_popup(
                self,
                popup_window,
                choice,
                *args,
                **kwargs
            )

    except Exception as exc:

        print(
            'WR9 POPUP ERROR:',
            repr(exc)
        )

    return None


# ============================================================
# INSTALL POPUP
# ============================================================

def start_test():

    global _original_popup
    global _popup_patched

    if _popup_patched:

        return

    try:

        cls = party.PartyWindow

        original = getattr(
            cls,
            'popup_menu_selected_choice',
            None
        )

        if not callable(original):

            print(
                'WR9 POPUP METHOD NOT FOUND'
            )

            return

        _original_popup = original

        cls.popup_menu_selected_choice = (
            popup_hook
        )

        _popup_patched = True

        print(
            'WR9 POPUP ACTIVE'
        )

    except Exception as exc:

        print(
            'WR9 POPUP ERROR:',
            repr(exc)
        )


# ============================================================
# ADD PANEL
# ============================================================

def open_add_panel():

    root = bui.containerwidget(
        size=(650, 450),
        transition='in_scale'
    )

    bui.textwidget(
        parent=root,
        position=(30, 375),
        size=(590, 45),
        text='ADD CUSTOM CODE',
        h_align='center',
        v_align='center',
        scale=0.70
    )

    bui.textwidget(
        parent=root,
        position=(50, 315),
        size=(550, 30),
        text='CODE',
        scale=0.45
    )

    code_field = bui.textwidget(
        parent=root,
        position=(50, 260),
        size=(550, 50),
        editable=True,
        text='',
        scale=0.55
    )

    bui.textwidget(
        parent=root,
        position=(50, 210),
        size=(550, 30),
        text='CUSTOM TEXT',
        scale=0.45
    )

    message_field = bui.textwidget(
        parent=root,
        position=(50, 145),
        size=(550, 55),
        editable=True,
        text='',
        scale=0.48
    )

    bui.textwidget(
        parent=root,
        position=(50, 100),
        size=(550, 30),
        text='{id} = ID     {name} = NAME',
        scale=0.40
    )

    def save():

        code = str(
            bui.textwidget(
                query=code_field
            )
        ).strip().lower().lstrip('%')

        text = str(
            bui.textwidget(
                query=message_field
            )
        )

        if not code:

            msg(
                'ENTER CODE'
            )

            return

        if not text:

            msg(
                'ENTER TEXT'
            )

            return

        if not re.match(
            r'^[a-zA-Z0-9_]+$',
            code
        ):

            msg(
                'INVALID CODE'
            )

            return

        CUSTOM_MESSAGES[code] = text

        if save_settings():

            bui.containerwidget(
                edit=root,
                transition='out_scale'
            )

            msg(
                'SAVED '
                + code.upper()
            )

    bui.buttonwidget(
        parent=root,
        position=(80, 35),
        size=(220, 55),
        label='SAVE',
        on_activate_call=save
    )

    bui.buttonwidget(
        parent=root,
        position=(370, 35),
        size=(220, 55),
        label='CANCEL',
        on_activate_call=lambda:
            bui.containerwidget(
                edit=root,
                transition='out_scale'
            )
    )


# ============================================================
# EDIT CODE
# ============================================================

def edit_code(code):

    if code not in CUSTOM_MESSAGES:

        return

    root = bui.containerwidget(
        size=(650, 400),
        transition='in_scale'
    )

    bui.textwidget(
        parent=root,
        position=(30, 325),
        size=(590, 45),
        text='EDIT ' + code.upper(),
        h_align='center',
        v_align='center',
        scale=0.70
    )

    field = bui.textwidget(
        parent=root,
        position=(50, 200),
        size=(550, 70),
        editable=True,
        text=CUSTOM_MESSAGES[code],
        scale=0.48
    )

    def save():

        CUSTOM_MESSAGES[code] = str(
            bui.textwidget(
                query=field
            )
        )

        save_settings()

        bui.containerwidget(
            edit=root,
            transition='out_scale'
        )

        msg(
            'UPDATED'
        )

    bui.buttonwidget(
        parent=root,
        position=(80, 55),
        size=(220, 60),
        label='SAVE',
        on_activate_call=save
    )

    bui.buttonwidget(
        parent=root,
        position=(370, 55),
        size=(220, 60),
        label='CANCEL',
        on_activate_call=lambda:
            bui.containerwidget(
                edit=root,
                transition='out_scale'
            )
    )


# ============================================================
# MAIN PANEL
# ============================================================

def open_panel():

    load_settings()

    root = bui.containerwidget(
        size=(700, 620),
        transition='in_scale'
    )

    bui.textwidget(
        parent=root,
        position=(30, 550),
        size=(640, 45),
        text='WR CUSTOM MESSAGES',
        h_align='center',
        v_align='center',
        scale=0.75
    )

    y = 455

    for code, text in CUSTOM_MESSAGES.items():

        preview = str(text)

        if len(preview) > 35:

            preview = (
                preview[:35]
                + '...'
            )

        bui.buttonwidget(
            parent=root,
            position=(50, y),
            size=(600, 58),
            label=(
                code.upper()
                + ' → '
                + preview
            ),
            on_activate_call=bui.Call(
                edit_code,
                code
            )
        )

        y -= 68

        if y < 120:

            break

    bui.buttonwidget(
        parent=root,
        position=(45, 30),
        size=(190, 55),
        label='ADD CODE',
        on_activate_call=open_add_panel
    )

    bui.buttonwidget(
        parent=root,
        position=(255, 30),
        size=(190, 55),
        label='START',
        on_activate_call=start_test
    )

    bui.buttonwidget(
        parent=root,
        position=(465, 30),
        size=(190, 55),
        label='CLOSE',
        on_activate_call=lambda:
            bui.containerwidget(
                edit=root,
                transition='out_scale'
            )
    )


# ============================================================
# WR BUTTON
# ============================================================

def _create_wr_button(window):

    global _WR_BUTTON

    try:

        root = getattr(
            window,
            '_root_widget',
            None
        )

        if root is None:

            print(
                'WR9 ROOT NOT FOUND'
            )

            return

        width = getattr(
            window,
            '_width',
            800
        )

        height = getattr(
            window,
            '_height',
            600
        )

        if not isinstance(
            width,
            (int, float)
        ):

            width = 800

        if not isinstance(
            height,
            (int, float)
        ):

            height = 600

        button_width = 75
        button_height = 34

        x = width - button_width - 2
        y = height - 85

        _WR_BUTTON = bui.buttonwidget(
            parent=root,
            position=(
                x,
                y
            ),
            size=(
                button_width,
                button_height
            ),
            label='WR',
            scale=1.0,
            on_activate_call=open_panel
        )

        print(
            'WR9 BUTTON CREATED:',
            x,
            y,
            'SIZE:',
            button_width,
            button_height
        )

    except Exception as exc:

        print(
            'WR9 CREATE BUTTON ERROR:',
            repr(exc)
        )


def add_button(original):

    def wrapper(
        self,
        *args,
        **kwargs
    ):

        result = original(
            self,
            *args,
            **kwargs
        )

        try:

            babase.apptimer(
                0.05,
                bui.Call(
                    _create_wr_button,
                    self
                )
            )

        except Exception as exc:

            print(
                'WR9 BUTTON TIMER ERROR:',
                repr(exc)
            )

        return result

    return wrapper


# ============================================================
# PLUGIN
# ============================================================

# ba_meta export plugin

class WRAutoSend(Plugin):

    def __init__(self):

        global _original_init
        global _button_installed

        print(
            'WR9 START'
        )

        load_settings()

        install_send()

        start_test()

        if not _button_installed:

            try:

                _original_init = (
                    party.PartyWindow.__init__
                )

                party.PartyWindow.__init__ = (
                    add_button(
                        _original_init
                    )
                )

                _button_installed = True

                print(
                    'WR9 BUTTON PATCHED'
                )

            except Exception as exc:

                print(
                    'WR9 INIT ERROR:',
                    repr(exc)
                )

        print(
            'WR API 9 / 1.7.62 READY'
        )