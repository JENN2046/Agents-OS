#!/usr/bin/python3
"""Native confirmation of the broker's fixed target. Never asks for a Key."""
import base64,hashlib,json,os,socket,stat,struct,sys
from datetime import datetime,timezone
SOCKET='/run/minimal-human-trust/approval.sock'
def confirmation_lane(argv):
    if argv==[]:return 'standard'
    if argv==['--first-cutover']:return 'first_cutover'
    raise RuntimeError('CONFIRMATION_ARGUMENTS_REFUSED')
def public_fingerprint(key):
    if not isinstance(key,str):raise RuntimeError('PUBLIC_KEY_REFUSED')
    try:raw=base64.b64decode(key+'='*((-len(key))%4),altchars=b'-_',validate=True)
    except Exception:raise RuntimeError('PUBLIC_KEY_REFUSED')
    if len(raw)!=44 or not raw.startswith(bytes.fromhex('302a300506032b6570032100')):
        raise RuntimeError('PUBLIC_KEY_REFUSED')
    return hashlib.sha256(raw).hexdigest()
def format_confirmation_summary(summary,proposal_hash):
    """Pure disclosure formatter. It neither verifies authority nor applies it."""
    if not isinstance(summary,dict) or not isinstance(proposal_hash,str) or len(proposal_hash)!=64 or any(c not in '0123456789abcdef' for c in proposal_hash):
        raise RuntimeError('CONFIRMATION_SUMMARY_REFUSED')
    action=summary.get('action')
    if action not in ['revoke_grant','create_grant','change_trust','enroll_human','first_cutover_handoff']:
        raise RuntimeError('CONFIRMATION_ACTION_REFUSED')
    cutover=action=='first_cutover_handoff'
    title='R17 · 首次恢复接管确认' if cutover else 'R16 · 确认授权操作'
    intro=('当前尚未执行接管。确认将授权下方固定发行内容的限定停业务、封锁旧写者和首次恢复接管；'
      '仍须通过真实三方 STOP、最终账本和单写者校验。'
      '\n保留两笔原始 UNKNOWN，不结算、不重放，不启用正常业务。'
      '\n新账本推进后，回滚须向前修复；不能让旧 Owner 直接覆盖新结果。'
      '\n确认只记录这笔授权，尚未应用。系统随后验证你的本机身份；不会要求输入 Key。') if cutover else (
      '核对下方完整操作和目标。确认后，系统将验证你的本机身份。'
      '\n不会要求输入 Key；确认只记录授权，尚未应用变更。')
    lines=['提案 SHA-256：'+proposal_hash]
    for field,label in [('issuedAt','签发时间（UTC）'),('expiresAt','截止时间（UTC）')]:
        value=summary.get(field)
        if value is not None:
            if isinstance(value,bool) or not isinstance(value,int) or value<=0:raise RuntimeError('CONFIRMATION_TIME_REFUSED')
            try:time=datetime.fromtimestamp(value/1000,timezone.utc).isoformat()
            except (OverflowError,ValueError,OSError):raise RuntimeError('CONFIRMATION_TIME_REFUSED')
            lines.append(label+'：'+time)
    if cutover:
        target=summary.get('target')
        if not isinstance(target,dict) or target.get('schema')!='mht.first-cutover-target.v1' or target.get('phase')!='FIRST_NATIVE_RECOVERY_CUTOVER':
            raise RuntimeError('CUTOVER_TARGET_REFUSED')
        template=target.get('newRootTemplate')
        if not isinstance(template,dict):raise RuntimeError('CUTOVER_TARGET_REFUSED')
        for field,label in [('oldRootHash','旧信任根 SHA-256'),('newRootTemplateHash','新公开模板 SHA-256')]:
            value=target.get(field)
            if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
                raise RuntimeError('CUTOVER_TARGET_REFUSED')
            lines.append(label+'：'+value)
        lines.append('接管前后保持同一组公开签发根；以下为 SPKI SHA-256 指纹：')
        for field,label in [('issuerPublicKey','Issuer 公钥 SPKI SHA-256'),('releasePublicKey','Release 公钥 SPKI SHA-256'),
          ('enrollmentAuthorityPublicKey','Enrollment 公钥 SPKI SHA-256')]:
            lines.append(label+'：'+public_fingerprint(template.get(field)))
    # Preserve every signed target field after the plain-language impact text.
    # No filter, truncation, renamed authority field, or hidden plan is used.
    lines.extend(['','完整待确认对象：',json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)])
    return {'title':title,'intro':intro,'details':'\n'.join(lines),
      'confirmLabel':'确认限定恢复接管并验证系统身份' if cutover else '确认这个操作并验证系统身份'}
def line(peer):
    raw=b''
    while b'\n' not in raw:
        part=peer.recv(4096)
        if not part or len(raw)+len(part)>16384:raise RuntimeError()
        raw+=part
    if not raw.endswith(b'\n') or raw.count(b'\n')!=1:raise RuntimeError()
    return json.loads(raw)
def main():
    lane=confirmation_lane(sys.argv[1:])
    if os.getuid()!=1000:raise RuntimeError()
    import tkinter as tk
    from tkinter import messagebox
    st=os.lstat(SOCKET)
    if not stat.S_ISSOCK(st.st_mode) or st.st_uid!=0 or st.st_mode&0o007:raise RuntimeError()
    peer=socket.socket(socket.AF_UNIX);peer.settimeout(175);peer.connect(SOCKET)
    if struct.unpack('3i',peer.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))[1]!=0:raise RuntimeError()
    peer.sendall((json.dumps({'operation':'select_confirmation','lane':lane})+'\n').encode())
    preview=line(peer)
    if preview.get('status')!='CONFIRM_EXACT_TARGET':raise RuntimeError()
    if (preview['summary'].get('action')=='first_cutover_handoff')!=(lane=='first_cutover'):raise RuntimeError()
    display=format_confirmation_summary(preview['summary'],preview['proposalHash'])
    window=tk.Tk();window.title(display['title'])
    tk.Label(window,text=display['intro'],justify='left',wraplength=760).pack(padx=18,pady=12)
    frame=tk.Frame(window);frame.pack(padx=18,fill='both',expand=True)
    scrollbar=tk.Scrollbar(frame);scrollbar.pack(side='right',fill='y')
    view=tk.Text(frame,width=90,height=24,wrap='word',yscrollcommand=scrollbar.set)
    view.insert('1.0',display['details']);view.configure(state='disabled');view.pack(side='left',fill='both',expand=True)
    scrollbar.configure(command=view.yview)
    def confirm():
        yes.configure(state='disabled')
        try:
            peer.sendall((json.dumps({'confirm':True,'proposalHash':preview['proposalHash'],'challenge':preview['challenge']})+'\n').encode())
            result=line(peer)
            if result.get('status')!='APPROVED_NOT_APPLIED' or result.get('proposalHash')!=preview['proposalHash']:raise RuntimeError()
            messagebox.showinfo('R16','授权确认已安全记录，尚未应用。',parent=window);window.destroy()
        except Exception:
            messagebox.showerror('R16','确认未完成或结果待核实。请勿重复操作；无需重新输入 Key。',parent=window);window.destroy()
        finally:peer.close()
    yes=tk.Button(window,text=display['confirmLabel'],command=confirm);yes.pack(pady=12)
    tk.Button(window,text='取消',command=lambda:(peer.close(),window.destroy())).pack(pady=6)
    window.mainloop()
if __name__=='__main__':
    try:main()
    except Exception:
        try:
            import tkinter as tk
            from tkinter import messagebox
            window=tk.Tk();window.withdraw();messagebox.showerror('R16','当前没有已认可的待确认操作，或可信授权入口尚未就绪。');window.destroy()
        except Exception:
            print('本机确认窗口尚未就绪；需要 Tkinter 和桌面会话。未完成授权。',file=sys.stderr)
        raise SystemExit(1)
