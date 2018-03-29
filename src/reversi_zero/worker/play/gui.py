# many code from http://d.hatena.ne.jp/yatt/20100129/1264791420
import os
from logging import getLogger

import wx
from wx.core import CommandEvent

from src.reversi_zero.config import Config
from src.reversi_zero.env.reversi.reversi_env import Player
from src.reversi_zero.lib.model_helpler import ask_model_dir
from src.reversi_zero.worker.play.game_model import PlayWithHuman, GameEvent

logger = getLogger(__name__)


def start(config: Config):
    model_dir = ask_model_dir(config)
    config.play_with_human_config.update_play_config(config.play)
    config.resource.model_config_path = os.path.join(model_dir, config.resource.model_config_filename)
    config.resource.model_weight_path = os.path.join(model_dir, config.resource.model_weight_filename)
    reversi_model = PlayWithHuman(config)
    app = wx.App()
    Frame(reversi_model, config.gui).Show()
    app.MainLoop()


def notify(caption, message):
    dialog = wx.MessageDialog(None, message=message, caption=caption, style=wx.OK)
    dialog.ShowModal()
    dialog.Destroy()


class Frame(wx.Frame):
    def __init__(self, model: PlayWithHuman, gui_config):
        self.model = model
        self.gui_config = gui_config
        self.is_flip_vertical = False
        wx.Frame.__init__(self, None, -1, self.gui_config.window_title, size=self.gui_config.window_size)
        # panel
        self.panel = wx.Panel(self)
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.try_move)
        self.panel.Bind(wx.EVT_PAINT, self.refresh)

        # menu bar
        menu = wx.Menu()
        menu.Append(1, u"New Game(Black)")
        menu.Append(2, u"New Game(White)")
        menu.AppendSeparator()
        menu.Append(5, u"Flip Vertical")
        menu.AppendSeparator()
        menu.Append(9, u"quit")
        menu_bar = wx.MenuBar()
        menu_bar.Append(menu, u"menu")
        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, self.handle_new_game, id=1)
        self.Bind(wx.EVT_MENU, self.handle_new_game, id=2)
        self.Bind(wx.EVT_MENU, self.handle_flip_vertical, id=5)
        self.Bind(wx.EVT_MENU, self.handle_quit, id=9)

        # status bar
        self.CreateStatusBar()

        self.model.add_observer(self.handle_game_event)

        self.new_game(human_is_black=True)

    def handle_game_event(self, event):
        if event == GameEvent.update:
            self.panel.Refresh()
            self.update_status_bar()
            wx.Yield()
        elif event == GameEvent.over:
            self.game_over()
        elif event == GameEvent.ai_move:
            self.ai_move()

    def handle_quit(self, event: CommandEvent):
        self.Close()

    def handle_new_game(self, event: CommandEvent):
        self.new_game(human_is_black=event.GetId() == 1)

    def handle_flip_vertical(self, event):
        self.is_flip_vertical = not self.is_flip_vertical
        self.panel.Refresh()

    def new_game(self, human_is_black):
        self.model.start_game(human_is_black=human_is_black)
        self.model.play_next_turn()

    def ai_move(self):
        self.panel.Refresh()
        self.update_status_bar()
        wx.Yield()
        self.model.move_by_ai()
        self.model.play_next_turn()

    def try_move(self, event):
        if self.model.over:
            return
        # calculate coordinate from window coordinate
        event_x, event_y = event.GetX(), event.GetY()
        w, h = self.panel.GetSize()
        x = int(event_x / (w / self.gui_config.EDGE_LENGTH))
        y = int(event_y / (h / self.gui_config.EDGE_LENGTH))

        if self.is_flip_vertical:
            y = self.gui_config.EDGE_LENGTH-1-y

        if not self.model.available(x, y):
            notify("fail", f'({x},{y}) is unavailable move.')
            return

        print(f'try to move {x} {y}')
        self.model.move(x, y)

        self.model.play_next_turn()

    def game_over(self):
        # if game is over then display dialog

        black, white = self.model.number_of_black_and_white
        mes = "black: %d\nwhite: %d\n" % (black, white)
        if black == white:
            mes += "** draw **"
        else:
            mes += "winner: %s" % ["black", "white"][black < white]
        notify("game is over", mes)
        # elif self.reversi.passed != None:
        #     notify("passing turn", "pass")

    def update_status_bar(self):
        msg = "current player is " + ["White", "Black"][self.model.next_player == Player.black]
        if self.model.ai_confidence:
            msg += f' | AI Confidence: [{self.model.ai_confidence[0]}, {self.model.ai_confidence[1]}]'
        self.SetStatusText(msg)

    def refresh(self, event):
        dc = wx.PaintDC(self.panel)
        self.update_status_bar()

        w, h = self.panel.GetSize()
        # background
        dc.SetBrush(wx.Brush("#228b22"))
        dc.DrawRectangle(0, 0, w, h)
        # grid
        dc.SetBrush(wx.Brush("black"))
        px, py = w / self.gui_config.EDGE_LENGTH, h / self.gui_config.EDGE_LENGTH
        for y in range(self.gui_config.EDGE_LENGTH):
            dc.DrawLine(y * px, 0, y * px, h)
            dc.DrawLine(0, y * py, w, y * py)
        dc.DrawLine(w - 1, 0, w - 1, h - 1)
        dc.DrawLine(0, h - 1, w - 1, h - 1)

        # stones
        brushes = {"white": wx.Brush("white"), "black": wx.Brush("black")}
        if self.gui_config.x_is_vertical:
            for x in range(self.gui_config.EDGE_LENGTH):
                vx = self.gui_config.EDGE_LENGTH-1-x if self.is_flip_vertical else x
                for y in range(self.gui_config.EDGE_LENGTH):
                    c = self.model.stone(x, y)
                    if c is not None:
                        dc.SetBrush(brushes[c])
                        dc.DrawEllipse(y * px, vx * py, py, px)
                    if hasattr(self.model, 'last_history') and self.model.last_history:
                        q_value = self.model.last_history.Q[x*self.gui_config.EDGE_LENGTH+y]
                        n_value = self.model.last_history.N[x*self.gui_config.EDGE_LENGTH+y]
                        v_value = self.model.last_history.V[x*self.gui_config.EDGE_LENGTH+y]
                        p_value = self.model.last_history.P[x*self.gui_config.EDGE_LENGTH+y]
                        if n_value:
                            dc.SetTextForeground(wx.Colour("blue"))
                            dc.DrawText(f"n={int(n_value):d}", y*px+2, vx*py+2)
                        if q_value:
                            dc.SetTextForeground(wx.Colour("blue"))
                            if q_value < 0:
                                dc.SetTextForeground(wx.Colour("red"))
                            dc.DrawText(f"q={q_value:.2f}", y*px+2, (vx+1)*py-16)
                        if v_value:
                            dc.SetTextForeground(wx.Colour("blue"))
                            if v_value < 0:
                                dc.SetTextForeground(wx.Colour("red"))
                            dc.DrawText(f"v={v_value:.1f}", (y+1)*px-46, vx*py+2)
                        if p_value:
                            dc.SetTextForeground(wx.Colour("blue"))
                            if p_value < 0:
                                dc.SetTextForeground(wx.Colour("red"))
                            dc.DrawText(f"p={p_value:.2f}", (y+1)*px-46, (vx+1)*py-16)
        else:
            for y in range(self.gui_config.EDGE_LENGTH):
                vy = self.gui_config.EDGE_LENGTH-1-y if self.is_flip_vertical else y
                for x in range(self.gui_config.EDGE_LENGTH):
                    c = self.model.stone(y, x)
                    if c is not None:
                        dc.SetBrush(brushes[c])
                        dc.DrawEllipse(x * px, vy * py, px, py)
                    if hasattr(self.model, 'last_history') and self.model.last_history:
                        q_value = self.model.last_history.Q[y*self.gui_config.EDGE_LENGTH+x]
                        n_value = self.model.last_history.N[y*self.gui_config.EDGE_LENGTH+x]
                        v_value = self.model.last_history.V[y*self.gui_config.EDGE_LENGTH+x]
                        p_value = self.model.last_history.P[y*self.gui_config.EDGE_LENGTH+x]
                        if n_value:
                            dc.SetTextForeground(wx.Colour("blue"))
                            if n_value:
                                dc.DrawText(f"{int(n_value):d}", x*px+2, vy*py+2)
                        if q_value:
                            dc.SetTextForeground(wx.Colour("blue"))
                            if q_value < 0:
                                dc.SetTextForeground(wx.Colour("red"))
                            dc.DrawText(f"{q_value:.2f}", x*px+2, (vy+1)*py-16)
                        if v_value:
                            dc.SetTextForeground(wx.Colour("blue"))
                            if v_value < 0:
                                dc.SetTextForeground(wx.Colour("red"))
                            dc.DrawText(f"v={v_value:.1f}", (x+1)*px-46, vy*py+2)
                        if p_value:
                            dc.SetTextForeground(wx.Colour("blue"))
                            if p_value < 0:
                                dc.SetTextForeground(wx.Colour("red"))
                            dc.DrawText(f"p={p_value:.2f}", (x+1)*px-46, (vy+1)*py-16)

