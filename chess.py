"""Шахматы вдвоём. Python 3, tkinter; без дополнительных пакетов."""
import tkinter as tk
from tkinter import messagebox
from collections import Counter
import copy

GLYPHS = dict(zip('KQRBNPkqrbnp', '♚♛♜♝♞♟♚♛♜♝♞♟'))
def side(p): return 'w' if p.isupper() else 'b'

class Game:
    def __init__(self):
        self.board = list('rnbqkbnrpppppppp' + '.'*32 + 'PPPPPPPPRNBQKBNR')
        self.turn, self.rights, self.ep, self.half = 'w', set('KQkq'), None, 0
        self.history, self.log = [], []
        self.counts = Counter({self.key(): 1})

    def key(self):
        ep = self.ep
        if ep is not None:
            pawn = 'P' if self.turn == 'w' else 'p'
            row = ep//8 + (1 if self.turn == 'w' else -1)
            valid = False
            for col in (ep%8-1, ep%8+1):
                if 0 <= row < 8 and 0 <= col < 8 and self.board[row*8+col] == pawn:
                    g = self.clone()
                    g.push(row*8+col, ep, 'Q')
                    if not g.check(self.turn): valid = True
            if not valid: ep = None
        return (''.join(self.board), self.turn, ''.join(sorted(self.rights)), ep)

    def clone(self):
        g = copy.copy(self)
        g.board, g.rights = self.board.copy(), self.rights.copy()
        return g

    def attacked(self, sq, by):
        r,c = divmod(sq,8)
        for i,p in enumerate(self.board):
            if p == '.' or side(p) != by: continue
            y,x = divmod(i,8)
            dr,dc,k = r-y,c-x,p.upper()
            if k == 'P' and dr == (-1 if by == 'w' else 1) and abs(dc) == 1: return True
            if k == 'N' and (abs(dr),abs(dc)) in ((1,2),(2,1)): return True
            if k == 'K' and max(abs(dr),abs(dc)) == 1: return True
            diag = abs(dr) == abs(dc) and dr != 0
            straight = (dr == 0) != (dc == 0)
            if (diag and k in 'BQ') or (straight and k in 'RQ'):
                sy,sx = (dr>0)-(dr<0),(dc>0)-(dc<0)
                y,x = y+sy,x+sx
                while (y,x) != (r,c) and self.board[y*8+x] == '.': y,x = y+sy,x+sx
                if (y,x) == (r,c): return True
        return False

    def check(self, who):
        return self.attacked(self.board.index('K' if who == 'w' else 'k'), 'b' if who == 'w' else 'w')

    def pseudo(self, src):
        p = self.board[src]
        if p == '.' or side(p) != self.turn: return []
        r,c = divmod(src,8)
        k, result = p.upper(), []
        if k == 'P':
            d = -1 if self.turn == 'w' else 1
            y = r+d
            if 0 <= y < 8:
                if self.board[y*8+c] == '.':
                    result.append(y*8+c)
                    if r == (6 if self.turn == 'w' else 1) and self.board[(r+2*d)*8+c] == '.': result.append((r+2*d)*8+c)
                for x in (c-1,c+1):
                    if 0 <= x < 8:
                        dst,t = y*8+x,self.board[y*8+x]
                        if (t != '.' and side(t) != self.turn and t.upper() != 'K') or dst == self.ep: result.append(dst)
            return result
        vectors = {'N':[(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)],
                   'B':[(1,1),(1,-1),(-1,1),(-1,-1)], 'R':[(1,0),(-1,0),(0,1),(0,-1)]}
        vectors['Q'] = vectors['B']+vectors['R']
        vectors['K'] = vectors['Q']
        for dr,dc in vectors[k]:
            y,x = r+dr,c+dc
            while 0 <= y < 8 and 0 <= x < 8:
                t = self.board[y*8+x]
                if t == '.': result.append(y*8+x)
                else:
                    if side(t) != self.turn and t.upper() != 'K': result.append(y*8+x)
                    break
                if k in 'NK': break
                y,x = y+dr,x+dc
        if k == 'K' and src == (60 if self.turn == 'w' else 4) and not self.check(self.turn):
            enemy = 'b' if self.turn == 'w' else 'w'
            for right,rook,empty,route,dst in [
                ('K' if self.turn == 'w' else 'k',src+3,[src+1,src+2],[src+1,src+2],src+2),
                ('Q' if self.turn == 'w' else 'q',src-4,[src-1,src-2,src-3],[src-1,src-2],src-2)]:
                if right in self.rights and self.board[rook] == ('R' if self.turn == 'w' else 'r') and all(self.board[s] == '.' for s in empty) and all(not self.attacked(s,enemy) for s in route): result.append(dst)
        return result

    def legal(self, src):
        result = []
        for dst in self.pseudo(src):
            g = self.clone()
            g.push(src,dst,'Q')
            if not g.check(self.turn): result.append(dst)
        return result

    def push(self, src, dst, promo):
        p,t = self.board[src],self.board[dst]
        if p.upper() == 'P' and dst == self.ep and t == '.':
            self.board[dst+(8 if p.isupper() else -8)] = '.'
            t = 'p'
        self.board[src],self.board[dst] = '.',p
        if p.upper() == 'K':
            self.rights.difference_update('KQ' if p.isupper() else 'kq')
            if abs(dst-src) == 2:
                rook = src+3 if dst>src else src-4
                self.board[(src+dst)//2],self.board[rook] = self.board[rook],'.'
        for sq,right in ((0,'q'),(7,'k'),(56,'Q'),(63,'K')):
            if sq in (src,dst): self.rights.discard(right)
        if p.upper() == 'P' and dst//8 in (0,7): self.board[dst] = promo if p.isupper() else promo.lower()
        self.ep = (src+dst)//2 if p.upper() == 'P' and abs(dst-src) == 16 else None
        self.half = 0 if p.upper() == 'P' or t != '.' else self.half+1
        self.turn = 'b' if self.turn == 'w' else 'w'

    def move(self, src, dst, promo='Q'):
        self.history.append((self.board.copy(),self.turn,self.rights.copy(),self.ep,self.half))
        p = self.board[src]
        capture = self.board[dst] != '.' or (p.upper() == 'P' and dst == self.ep)
        text = self.square(src)+(' × ' if capture else ' — ')+self.square(dst)
        if p.upper() == 'K' and abs(dst-src) == 2: text = 'O-O' if dst>src else 'O-O-O'
        if p.upper() == 'P' and dst//8 in (0,7): text += '='+promo
        self.push(src,dst,promo)
        if self.check(self.turn): text += '+'
        self.log.append(text)
        self.counts[self.key()] += 1

    def undo(self):
        if self.history:
            self.counts[self.key()] -= 1
            self.board,self.turn,self.rights,self.ep,self.half = self.history.pop()
            self.log.pop()

    @staticmethod
    def square(i): return 'abcdefgh'[i%8]+str(8-i//8)

    def status(self):
        checked = self.check(self.turn)
        if not any(self.legal(i) for i,p in enumerate(self.board) if p != '.' and side(p) == self.turn):
            return ('Мат! Победили '+('чёрные' if self.turn == 'w' else 'белые') if checked else 'Ничья — пат'),True
        pieces = [(i,p.upper()) for i,p in enumerate(self.board) if p != '.' and p.upper() != 'K']
        insufficient = not pieces or (len(pieces) == 1 and pieces[0][1] in 'BN')
        if pieces and all(p == 'B' for _,p in pieces): insufficient = len({(i//8+i%8)%2 for i,_ in pieces}) == 1
        if insufficient: return 'Ничья — недостаточно фигур',True
        if self.half >= 150 or self.counts[self.key()] >= 5: return 'Ничья — '+('правило 75 ходов' if self.half >= 150 else 'пятикратное повторение'),True
        return ('Ход белых' if self.turn == 'w' else 'Ход чёрных')+(' • ШАХ' if checked else ''),False

class App:
    BG,PANEL,TEXT,MUTED,ACCENT = '#151b27','#202938','#edf1f7','#99a7bb','#6bd6b4'
    def __init__(self, root):
        self.root = root
        root.title('Шахматы • игра вдвоём')
        root.configure(bg=self.BG)
        root.geometry('1080x800')
        root.minsize(850,650)
        self.game = Game()
        self.selected,self.targets,self.drag = None,[],None
        self.flipped,self.finished,self.agreed = False,False,None
        panel = tk.Frame(root,bg=self.PANEL,width=280,padx=24,pady=26)
        panel.pack(side='right',fill='y',padx=(0,20),pady=20)
        panel.pack_propagate(False)
        def label(text,size,color):
            w = tk.Label(panel,text=text,font=('Segoe UI',size),bg=self.PANEL,fg=color,anchor='w',justify='left',wraplength=230)
            w.pack(fill='x',pady=(0,12))
            return w
        label('ШАХМАТЫ',23,self.TEXT)
        label('Два игрока • один экран',10,self.MUTED)
        self.status_label = label('',15,self.ACCENT)
        label('Перетащите фигуру или\nвыберите её и клетку хода.',10,self.MUTED)
        for title,fn in [('Новая партия',self.new),('Отменить ход',self.undo),('Перевернуть доску',self.flip),('Предложить ничью',self.draw)]:
            tk.Button(panel,text=title,command=fn,bg='#303d51',fg=self.TEXT,activebackground='#42556c',activeforeground='white',relief='flat',bd=0,font=('Segoe UI',11),cursor='hand2',pady=9).pack(fill='x',pady=4)
        label('История ходов',12,self.TEXT)
        self.moves = tk.Text(panel,bg=self.PANEL,fg=self.MUTED,font=('Consolas',11),relief='flat',state='disabled',wrap='word',width=20,height=8)
        self.moves.pack(fill='both',expand=True)
        label('Ctrl+Z — отмена • Esc — снять выбор',9,self.MUTED)
        self.canvas = tk.Canvas(root,bg=self.BG,highlightthickness=0)
        self.canvas.pack(fill='both',expand=True,padx=15,pady=15)
        self.canvas.bind('<Configure>',lambda e:self.render())
        self.canvas.bind('<ButtonPress-1>',self.press)
        self.canvas.bind('<B1-Motion>',self.motion)
        self.canvas.bind('<ButtonRelease-1>',self.release)
        root.bind('<Control-z>',lambda e:self.undo())
        root.bind('<Escape>',lambda e:self.clear())
        self.refresh()

    def clear(self):
        self.selected,self.targets,self.drag = None,[],None
        self.render()

    def refresh(self):
        text,self.finished = self.game.status()
        if self.agreed: text,self.finished = self.agreed,True
        self.status_label.config(text=text)
        self.moves.config(state='normal')
        self.moves.delete('1.0','end')
        for i in range(0,len(self.game.log),2):
            self.moves.insert('end',f'{i//2+1:>2}. {self.game.log[i]}\n')
            if i+1 < len(self.game.log): self.moves.insert('end',f'    {self.game.log[i+1]}\n')
        self.moves.see('end')
        self.moves.config(state='disabled')
        self.render()

    def position(self, sq):
        v = 63-sq if self.flipped else sq
        return self.ox+(v%8+.5)*self.cell,self.oy+(v//8+.5)*self.cell

    def hit(self, x, y):
        c,r = int((x-self.ox)//self.cell),int((y-self.oy)//self.cell)
        if not (0 <= c < 8 and 0 <= r < 8): return None
        return 63-(r*8+c) if self.flipped else r*8+c

    def piece(self, sq, x, y, tag='piece'):
        p = self.game.board[sq]
        fill,outline = ('#fff7e7','#384254') if p.isupper() else ('#202b3b','#c4d1df')
        font = ('Segoe UI Symbol',max(18,int(self.cell*.64)))
        for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
            self.canvas.create_text(x+dx,y+dy,text=GLYPHS[p],font=font,fill=outline,tags=tag)
        self.canvas.create_text(x,y,text=GLYPHS[p],font=font,fill=fill,tags=tag)

    def render(self):
        cv = self.canvas
        cv.delete('all')
        w,h = max(cv.winfo_width(),100),max(cv.winfo_height(),100)
        self.cell = max(1,(min(w,h)-52)/8)
        self.ox,self.oy = (w-8*self.cell)/2,(h-8*self.cell)/2
        last = self.game.history[-1][0] if self.game.history else None
        checked = self.game.board.index('K' if self.game.turn == 'w' else 'k') if self.game.check(self.game.turn) else None
        for sq,p in enumerate(self.game.board):
            x,y = self.position(sq)
            color = '#dce4df' if (sq//8+sq%8)%2 == 0 else '#6f9388'
            if last and p != last[sq]: color = '#b4c680'
            if sq == self.selected: color = '#e8c76e'
            if sq == checked: color = '#d47777'
            d = self.cell/2
            cv.create_rectangle(x-d,y-d,x+d,y+d,fill=color,outline='')
            if sq in self.targets:
                if p == '.': cv.create_oval(x-5,y-5,x+5,y+5,fill='#315c50',outline='')
                else: cv.create_oval(x-d+4,y-d+4,x+d-4,y+d-4,outline='#e4b65d',width=4)
            if p != '.' and not (self.drag and sq == self.selected): self.piece(sq,x,y)
        for k in range(8):
            file = 'hgfedcba'[k] if self.flipped else 'abcdefgh'[k]
            rank = str(k+1 if self.flipped else 8-k)
            cv.create_text(self.ox+(k+.5)*self.cell,self.oy+8*self.cell+17,text=file,fill=self.MUTED,font=('Segoe UI',11))
            cv.create_text(self.ox-17,self.oy+(k+.5)*self.cell,text=rank,fill=self.MUTED,font=('Segoe UI',11))
        if self.drag: self.piece(self.selected,*self.drag,tag='drag')

    def press(self, e):
        if self.finished: return
        sq = self.hit(e.x,e.y)
        if sq is None:
            self.clear()
            return
        if self.selected is not None and sq in self.targets:
            self.commit(sq)
            return
        p = self.game.board[sq]
        if p != '.' and side(p) == self.game.turn:
            self.selected,self.targets = sq,self.game.legal(sq)
            self.drag = (e.x,e.y)
            self.render()
        else: self.clear()

    def motion(self, e):
        if self.drag:
            self.drag = (e.x,e.y)
            self.canvas.delete('drag')
            self.piece(self.selected,e.x,e.y,'drag')

    def release(self, e):
        if self.drag:
            self.drag = None
            dst = self.hit(e.x,e.y)
            if dst in self.targets: self.commit(dst)
            else: self.render()

    def promote(self):
        dialog = tk.Toplevel(self.root)
        dialog.title('Превращение пешки')
        dialog.configure(bg=self.PANEL)
        dialog.resizable(False,False)
        dialog.transient(self.root)
        choice = ['Q']
        tk.Label(dialog,text='Выберите новую фигуру',bg=self.PANEL,fg=self.TEXT,font=('Segoe UI',14),padx=25,pady=18).pack()
        row = tk.Frame(dialog,bg=self.PANEL)
        row.pack(padx=15,pady=(0,20))
        def pick(p):
            choice[0] = p
            dialog.destroy()
        for p,name in [('Q','Ферзь'),('R','Ладья'),('B','Слон'),('N','Конь')]:
            tk.Button(row,text=GLYPHS[p]+'\n'+name,font=('Segoe UI Symbol',16),command=lambda p=p:pick(p),width=7,bg='#dce4df',relief='flat').pack(side='left',padx=4)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return choice[0]

    def commit(self, dst):
        src = self.selected
        promo = self.promote() if self.game.board[src].upper() == 'P' and dst//8 in (0,7) else 'Q'
        self.game.move(src,dst,promo)
        self.selected,self.targets,self.drag = None,[],None
        self.refresh()

    def new(self):
        if not self.game.history or messagebox.askyesno('Новая партия','Начать новую партию?',parent=self.root):
            self.game,self.agreed = Game(),None
            self.selected,self.targets,self.drag = None,[],None
            self.refresh()

    def undo(self):
        self.game.undo()
        self.agreed = None
        self.selected,self.targets,self.drag = None,[],None
        self.refresh()

    def flip(self):
        self.flipped = not self.flipped
        self.clear()

    def draw(self):
        if self.finished: return
        claim = self.game.half >= 100 or self.game.counts[self.game.key()] >= 3
        text = 'Зафиксировать ничью по правилу 50 ходов или троекратного повторения?' if claim else 'Второй игрок согласен на ничью?'
        if messagebox.askyesno('Ничья',text,parent=self.root):
            self.agreed = 'Ничья — '+('по заявлению' if claim else 'по соглашению')
            self.clear()
            self.refresh()


# LAN transport: newline-delimited JSON, UDP presence, TCP game channel.
import socket
import threading
import queue
import json
import time
import uuid
import hashlib
from tkinter import simpledialog

LAN_PORT = 47853
LAN_MAGIC = 'chess-lan-2026-v1'

class Channel:
    def __init__(self, owner, sock):
        self.owner, self.sock = owner, sock
        self.lock = threading.Lock()
        self.closed = False
        self.last = time.monotonic()
        sock.settimeout(1)
    def send(self, packet):
        try:
            data = (json.dumps(packet, ensure_ascii=False)+'\n').encode('utf-8')
            with self.lock:
                if self.closed: return False
                self.sock.sendall(data)
            return True
        except OSError:
            self.close()
            return False
    def close(self):
        if not self.closed:
            self.closed = True
            try: self.sock.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            self.sock.close()
            self.owner.events.put(('lost', self, None))
    def read(self):
        buffer = b''
        try:
            while not self.closed and not self.owner.stopped.is_set():
                try: data = self.sock.recv(4096)
                except socket.timeout:
                    if time.monotonic()-self.last > 18: break
                    continue
                if not data: break
                self.last = time.monotonic()
                buffer += data
                if len(buffer) > 16384: break
                while b'\n' in buffer:
                    line,buffer = buffer.split(b'\n',1)
                    packet = json.loads(line)
                    if not isinstance(packet,dict): raise ValueError('packet')
                    kind = packet.get('type')
                    if kind == 'ping': self.send({'type':'pong'})
                    elif kind != 'pong': self.owner.events.put(('packet',self,packet))
        except (OSError,ValueError,UnicodeError): pass
        finally: self.close()

class LAN:
    def __init__(self, name, discovery_port=LAN_PORT):
        self.name, self.port = name[:40], discovery_port
        self.ident = uuid.uuid4().hex
        self.events = queue.Queue()
        self.stopped = threading.Event()
        self.busy = False
        self.channels = set()
        self.peers = {}
        self.peer_lock = threading.Lock()
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server.bind(('',0))
        self.server.listen(8)
        self.server.settimeout(1)
        self.tcp_port = self.server.getsockname()[1]
        self.udp = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.udp.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.udp.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        try:
            self.udp.bind(('',self.port))
            self.udp.settimeout(1)
        except OSError:
            self.udp.close()
            self.server.close()
            raise
        for target in (self.accept_loop,self.discovery_loop,self.beacon_loop):
            threading.Thread(target=target,daemon=True).start()
    def adopt(self, sock):
        channel = Channel(self,sock)
        self.channels.add(channel)
        threading.Thread(target=channel.read,daemon=True).start()
        return channel
    def accept_loop(self):
        while not self.stopped.is_set():
            try:
                sock,addr = self.server.accept()
                if len([c for c in self.channels if not c.closed]) >= 8: sock.close()
                else: self.adopt(sock)
            except socket.timeout: continue
            except OSError: break
    def connect(self, host, port):
        def run():
            try:
                sock = socket.create_connection((host,port),timeout=5)
                ch = self.adopt(sock)
                self.events.put(('connected',ch,None))
            except OSError as e: self.events.put(('error',None,str(e)))
        threading.Thread(target=run,daemon=True).start()
    def presence(self):
        return {'magic':LAN_MAGIC,'id':self.ident,'name':self.name,'port':self.tcp_port,'busy':self.busy}
    def beacon_loop(self):
        while not self.stopped.is_set():
            data = json.dumps(self.presence()).encode()
            for addr in ('255.255.255.255','127.255.255.255'):
                try: self.udp.sendto(data,(addr,self.port))
                except OSError: pass
            for ch in list(self.channels):
                if ch.closed: self.channels.discard(ch)
                else: ch.send({'type':'ping'})
            self.stopped.wait(2)
    def discovery_loop(self):
        while not self.stopped.is_set():
            try:
                data,addr = self.udp.recvfrom(4096)
                p = json.loads(data)
                if not isinstance(p,dict) or p.get('magic') != LAN_MAGIC or p.get('id') == self.ident: continue
                if not isinstance(p.get('id'),str) or not isinstance(p.get('name'),str): continue
                if type(p.get('port')) is not int or not 1 <= p['port'] <= 65535: continue
                with self.peer_lock:
                    old = self.peers.get(p['id'])
                    ip = old[1] if old and addr[0].startswith('127.') and not old[1].startswith('127.') else addr[0]
                    self.peers[p['id']] = (p['name'][:40],ip,p['port'],bool(p.get('busy')),time.monotonic())
            except socket.timeout: continue
            except (ValueError,UnicodeError): continue
            except OSError: break
    def players(self):
        with self.peer_lock:
            return sorted([(ident,*p[:4]) for ident,p in self.peers.items() if time.monotonic()-p[4] < 7],key=lambda p:p[1])
    def close(self):
        self.stopped.set()
        self.server.close()
        self.udp.close()
        for ch in list(self.channels): ch.close()

class LANApp(App):
    def __init__(self, root):
        self.net = None
        self.channel = None
        self.outgoing = None
        self.lan_active = False
        self.my_color = None
        self.pending = None
        self.inviting = False
        self.revision = 0
        self.lobby = None
        self.opponent = ''
        super().__init__(root)
        root.title('Шахматы • вдвоём и по LAN')
        root.geometry('1120x880')
        root.minsize(900,820)
        panel = self.status_label.master
        self.lan_label = tk.Label(panel,text='Игра на одном ПК',bg=self.PANEL,fg=self.ACCENT,font=('Segoe UI',10),wraplength=230,justify='left')
        self.lan_label.pack(before=self.status_label,fill='x',pady=(0,8))
        self.lan_button = tk.Button(panel,text='Играть по сети LAN',command=self.open_lobby,bg='#336758',fg='white',activebackground='#428573',font=('Segoe UI',11),relief='flat',pady=9)
        self.lan_button.pack(before=self.status_label,fill='x',pady=(0,12))
        root.protocol('WM_DELETE_WINDOW',self.shutdown)
        root.after(100,self.poll)

    def digest(self):
        state = [self.game.key(),self.game.half,self.game.log,self.revision,self.agreed]
        return hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()

    def refresh(self):
        super().refresh()
        if self.lan_active and hasattr(self,'lan_label'):
            color = 'белые' if self.my_color == 'w' else 'чёрные'
            status = ' • ваш ход' if self.game.turn == self.my_color else ' • ход друга'
            if not self.channel or self.channel.closed: status = ' • связь потеряна'
            elif self.pending: status = ' • ожидаем ответ'
            self.lan_label.config(text=f'{self.opponent}\nВы — {color}{status}')

    def open_lobby(self):
        if self.lan_active:
            if not messagebox.askyesno('Выйти из LAN','Завершить сетевую партию и вернуться к игре на одном ПК?',parent=self.root): return
            self.leave()
        if not self.net:
            try: self.net = LAN(socket.gethostname())
            except OSError as e:
                messagebox.showerror('Сеть LAN',f'Не удалось запустить поиск игроков:\n{e}',parent=self.root)
                return
        if self.lobby and self.lobby.winfo_exists():
            self.lobby.lift()
            return
        win = self.lobby = tk.Toplevel(self.root)
        win.title('Игроки в локальной сети')
        win.geometry('590x530')
        win.configure(bg=self.PANEL)
        win.transient(self.root)
        def lbl(text):
            tk.Label(win,text=text,bg=self.PANEL,fg=self.TEXT,font=('Segoe UI',11),wraplength=540,justify='left').pack(anchor='w',padx=22,pady=8)
        lbl('Игроки появляются автоматически, когда открывают окно LAN.\nВыберите друга и отправьте приглашение.')
        addresses = sorted({a[4][0] for a in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET) if not a[4][0].startswith('127.')})
        lbl('Вы: '+self.net.name+'\nАдрес: '+', '.join(f'{ip}:{self.net.tcp_port}' for ip in addresses))
        self.peer_list = tk.Listbox(win,bg=self.BG,fg=self.TEXT,selectbackground='#336758',font=('Segoe UI',12),relief='flat',height=8,exportselection=False)
        self.peer_list.pack(fill='both',expand=True,padx=22,pady=8)
        self.peer_list.bind('<Double-Button-1>',lambda e:self.invite_selected())
        self.lobby_status = tk.StringVar(value='Ищем игроков…')
        tk.Label(win,textvariable=self.lobby_status,bg=self.PANEL,fg=self.ACCENT,font=('Segoe UI',10),wraplength=540).pack(padx=22,pady=5)
        for text,fn in [('Пригласить выбранного игрока',self.invite_selected),('Подключиться по IP и порту',self.direct),('Изменить своё имя',self.rename)]:
            tk.Button(win,text=text,command=fn,bg='#303d51',fg=self.TEXT,relief='flat',font=('Segoe UI',11),pady=6).pack(fill='x',padx=22,pady=4)
        self.peer_rows = []
        self.update_lobby()

    def update_lobby(self):
        if not self.lobby or not self.lobby.winfo_exists(): return
        rows = self.net.players()
        if rows != getattr(self,'peer_rows',[]):
            selected = self.peer_list.curselection()
            ident = self.peer_rows[selected[0]][0] if selected and selected[0] < len(self.peer_rows) else None
            self.peer_list.delete(0,'end')
            for i,(uid,name,ip,port,busy) in enumerate(rows):
                self.peer_list.insert('end',f'{name}  •  {ip}  •  '+('занят' if busy else 'готов к игре'))
                if uid == ident: self.peer_list.selection_set(i)
            self.peer_rows = rows
        if not self.net.busy: self.lobby_status.set('Выберите игрока' if rows else 'Ищем игроков… Откройте LAN на втором ПК.')
        self.root.after(1000,self.update_lobby)

    def rename(self):
        name = simpledialog.askstring('Имя игрока','Как вас показать другим игрокам?',initialvalue=self.net.name,parent=self.lobby)
        if name and name.strip(): self.net.name = name.strip()[:40]

    def direct(self):
        addr = simpledialog.askstring('Прямое подключение','Введите IP:порт из окна LAN друга:',parent=self.lobby)
        if not addr: return
        try:
            ip,port = addr.strip().rsplit(':',1)
            socket.inet_aton(ip)
            port = int(port)
            if not 1 <= port <= 65535: raise ValueError()
        except (ValueError,OSError):
            messagebox.showerror('Адрес','Пример: 192.168.1.15:54321',parent=self.lobby)
            return
        self.invite(ip,port)

    def invite_selected(self):
        selection = self.peer_list.curselection()
        if not selection: return
        _,name,ip,port,busy = self.peer_rows[selection[0]]
        if busy:
            self.lobby_status.set('Этот игрок сейчас занят.')
            return
        self.invite(ip,port)

    def invite(self, ip, port):
        if self.net.busy: return
        self.net.busy = True
        self.inviting = True
        self.notice('Подключаемся и отправляем приглашение…')
        self.net.connect(ip,port)
        self.root.after(35000,self.invite_timeout)

    def invite_timeout(self):
        if self.inviting and not self.lan_active:
            self.inviting = False
            self.net.busy = False
            if self.outgoing: self.outgoing.close()
            self.outgoing = None
            self.notice('Приглашение истекло. Попробуйте ещё раз.')

    def notice(self, text):
        if self.lobby and self.lobby.winfo_exists(): self.lobby_status.set(text)

    def poll(self):
        if self.net:
            for _ in range(100):
                try: event,ch,data = self.net.events.get_nowait()
                except queue.Empty: break
                if event == 'connected':
                    if not self.inviting: ch.close(); continue
                    self.outgoing = ch
                    ch.send({'type':'invite','magic':LAN_MAGIC,'name':self.net.name})
                    self.notice('Приглашение отправлено. Ждём подтверждения друга…')
                elif event == 'error':
                    if self.inviting:
                        self.net.busy,self.inviting = False,False
                        self.notice('Не удалось подключиться: '+data)
                elif event == 'lost':
                    if ch is self.channel:
                        self.channel = None
                        self.pending = None
                        self.clear()
                        self.refresh()
                        messagebox.showwarning('Связь потеряна','Связь с другом потеряна. Партия остановлена.\nНажмите «Выйти из LAN», чтобы начать заново.',parent=self.root)
                    elif ch is self.outgoing:
                        self.outgoing = None
                        self.inviting = False
                        self.net.busy = self.lan_active
                        self.notice('Приглашение отклонено или соединение закрыто.')
                elif event == 'packet': self.packet(ch,data)
        self.root.after(100,self.poll)

    def packet(self, ch, p):
        kind = p.get('type')
        if kind == 'invite':
            if p.get('magic') != LAN_MAGIC or not isinstance(p.get('name'),str): ch.close(); return
            if self.net.busy:
                ch.send({'type':'reject','reason':'Игрок занят'})
                ch.close()
                return
            self.net.busy = True
            name = p['name'][:40]
            self.root.bell()
            accepted = messagebox.askyesno('Приглашение в шахматы',f'{name} приглашает вас сыграть по LAN.\nПринять? Вы будете играть чёрными.',parent=self.root)
            if accepted and not ch.closed:
                if ch.send({'type':'accept','name':self.net.name,'magic':LAN_MAGIC}): self.start_match(ch,'b',name)
                else: self.net.busy = False
            else:
                ch.send({'type':'reject','reason':'Приглашение отклонено'})
                ch.close()
                self.net.busy = False
            return
        if kind == 'accept' and ch is self.outgoing and self.inviting:
            if p.get('magic') != LAN_MAGIC or not isinstance(p.get('name'),str): ch.close(); return
            self.start_match(ch,'w',p['name'][:40])
            return
        if kind == 'reject' and ch is self.outgoing:
            self.notice(str(p.get('reason','Приглашение отклонено'))[:100])
            ch.close()
            return
        if ch is not self.channel: ch.close(); return
        if kind == 'move':
            s,d,promo = p.get('src'),p.get('dst'),p.get('promo')
            valid = (not self.finished and (not self.pending or self.pending[0] == 'outgoing') and self.game.turn != self.my_color and p.get('rev') == self.revision and p.get('hash') == self.digest() and type(s) is int and type(d) is int and 0 <= s < 64 and 0 <= d < 64 and isinstance(promo,str) and promo in ('Q','R','B','N'))
            if not valid or d not in self.game.legal(s): self.protocol_error(); return
            self.pending = None
            self.game.move(s,d,promo)
            self.revision += 1
            self.clear(); self.refresh()
        elif kind == 'request':
            action,ident = p.get('action'),p.get('id')
            valid = action in ('new','undo','draw') and isinstance(ident,str) and len(ident) <= 40
            if not valid: self.protocol_error(); return
            if self.pending or p.get('rev') != self.revision or p.get('hash') != self.digest():
                ch.send({'type':'answer','id':ident,'ok':False})
                return
            self.pending = ('incoming',ident,action)
            self.clear(); self.refresh()
            text = {'new':'Друг предлагает начать новую партию. Согласны?','undo':'Друг просит отменить последний ход. Согласны?','draw':'Друг предлагает ничью. Согласны?'}[action]
            ok = messagebox.askyesno('Предложение друга',text,parent=self.root)
            if ch.send({'type':'answer','id':ident,'ok':ok}) and ok: self.apply_action(action)
            self.pending = None
            self.refresh()
        elif kind == 'answer':
            if self.pending and self.pending[0] == 'outgoing' and p.get('id') == self.pending[1]:
                if p.get('ok') is True: self.apply_action(self.pending[2])
                self.pending = None
                self.refresh()
        elif kind == 'claim':
            if self.finished or p.get('rev') != self.revision or p.get('hash') != self.digest() or not (self.game.half >= 100 or self.game.counts[self.game.key()] >= 3): self.protocol_error(); return
            self.apply_action('draw')
        else: self.protocol_error()

    def protocol_error(self):
        if self.channel: self.channel.close()

    def start_match(self, ch, color, name):
        self.channel,self.my_color,self.opponent = ch,color,name
        self.outgoing,self.inviting,self.pending = None,False,None
        self.lan_active,self.net.busy = True,True
        self.game,self.agreed,self.revision = Game(),None,0
        self.flipped = color == 'b'
        self.lan_button.config(text='Выйти из LAN')
        if self.lobby and self.lobby.winfo_exists(): self.lobby.destroy()
        self.clear(); self.refresh()

    def can_play(self):
        return not self.lan_active or (self.channel and not self.channel.closed and not self.pending and self.game.turn == self.my_color)

    def press(self, e):
        if self.can_play(): super().press(e)

    def commit(self, dst):
        if not self.can_play(): return
        if not self.lan_active: return super().commit(dst)
        src = self.selected
        if src is None or dst not in self.game.legal(src): return
        promo = self.promote() if self.game.board[src].upper() == 'P' and dst//8 in (0,7) else 'Q'
        packet = {'type':'move','src':src,'dst':dst,'promo':promo,'rev':self.revision,'hash':self.digest()}
        if self.channel.send(packet):
            self.game.move(src,dst,promo)
            self.revision += 1
        self.clear(); self.refresh()

    def ask_action(self, action):
        if not self.channel or self.channel.closed or self.pending: return
        if action == 'undo' and not self.game.history: return
        ident = uuid.uuid4().hex
        self.pending = ('outgoing',ident,action)
        self.channel.send({'type':'request','action':action,'id':ident,'rev':self.revision,'hash':self.digest()})
        self.clear(); self.refresh()
        def timeout():
            if self.pending and self.pending[1] == ident:
                # Close rather than risk applying a late answer to a different position.
                self.channel.close() if self.channel else None
        self.root.after(60000,timeout)

    def apply_action(self, action):
        if action == 'new':
            self.game,self.agreed = Game(),None
        elif action == 'undo':
            self.game.undo(); self.agreed = None
        else: self.agreed = 'Ничья — по соглашению или заявлению'
        self.revision += 1
        self.clear(); self.refresh()

    def new(self):
        if self.lan_active: self.ask_action('new')
        else: super().new()
    def undo(self):
        if self.lan_active: self.ask_action('undo')
        else: super().undo()
    def draw(self):
        if not self.lan_active: return super().draw()
        if self.finished or self.pending or not self.channel or self.channel.closed: return
        if self.game.half >= 100 or self.game.counts[self.game.key()] >= 3:
            if self.channel.send({'type':'claim','rev':self.revision,'hash':self.digest()}): self.apply_action('draw')
        else: self.ask_action('draw')

    def leave(self):
        ch,self.channel = self.channel,None
        self.lan_active,self.my_color,self.pending = False,None,None
        if ch: ch.close()
        if self.net: self.net.busy = False
        self.game,self.agreed,self.revision = Game(),None,0
        self.lan_button.config(text='Играть по сети LAN')
        self.lan_label.config(text='Игра на одном ПК')
        self.clear(); self.refresh()

    def shutdown(self):
        if self.net: self.net.close()
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    LANApp(root)
    root.mainloop()
