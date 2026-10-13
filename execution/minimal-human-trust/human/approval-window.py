#!/usr/bin/python3
"""Native confirmation of the broker's fixed target. Never asks for a Key."""
import json,os,socket,stat,struct,sys,tkinter as tk
from tkinter import messagebox
SOCKET='/run/minimal-human-trust/approval.sock'
def line(peer):
    raw=b''
    while b'\n' not in raw:
        part=peer.recv(4096)
        if not part or len(raw)+len(part)>16384:raise RuntimeError()
        raw+=part
    if not raw.endswith(b'\n') or raw.count(b'\n')!=1:raise RuntimeError()
    return json.loads(raw)
def main():
    if len(sys.argv)!=1 or os.getuid()!=1000:raise RuntimeError()
    st=os.lstat(SOCKET)
    if not stat.S_ISSOCK(st.st_mode) or st.st_uid!=0 or st.st_mode&0o007:raise RuntimeError()
    peer=socket.socket(socket.AF_UNIX);peer.settimeout(175);peer.connect(SOCKET)
    if struct.unpack('3i',peer.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))[1]!=0:raise RuntimeError()
    preview=line(peer)
    if preview.get('status')!='CONFIRM_EXACT_TARGET':raise RuntimeError()
    window=tk.Tk();window.title('R16 · 确认授权操作')
    tk.Label(window,text='核对下方操作和目标。确认后，系统将验证你的本机身份。\n不会输入 Key；确认也不会自动部署或应用变更。',justify='left').pack(padx=18,pady=12)
    view=tk.Text(window,width=90,height=24,wrap='word');view.insert('1.0',json.dumps(preview['summary'],ensure_ascii=False,indent=2));view.configure(state='disabled');view.pack(padx=18)
    def confirm():
        yes.configure(state='disabled')
        try:
            peer.sendall((json.dumps({'confirm':True,'proposalHash':preview['proposalHash'],'challenge':preview['challenge']})+'\n').encode())
            result=line(peer)
            if result.get('status')!='APPROVED_NOT_APPLIED':raise RuntimeError()
            messagebox.showinfo('R16','授权确认已安全记录，尚未应用。',parent=window);window.destroy()
        except Exception:
            messagebox.showerror('R16','确认未完成或结果待核实。请勿重复操作；无需重新输入 Key。',parent=window);window.destroy()
        finally:peer.close()
    yes=tk.Button(window,text='确认这个操作并验证系统身份',command=confirm);yes.pack(pady=12)
    tk.Button(window,text='取消',command=lambda:(peer.close(),window.destroy())).pack(pady=6)
    window.mainloop()
if __name__=='__main__':
    try:main()
    except Exception:
        window=tk.Tk();window.withdraw();messagebox.showerror('R16','当前没有已认可的待确认操作，或可信授权入口尚未就绪。');window.destroy();raise SystemExit(1)
