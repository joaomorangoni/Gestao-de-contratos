import type {ReactNode} from 'react';
import {X} from 'lucide-react';
import type {Status} from './types';
export const statusLabels: Record<Status, string> = {EM_APROVACAO:'Em aprovação', REPROVADO:'Reprovado', APROVADO:'Aprovado', EM_ASSINATURA:'Em assinatura', ASSINADO:'Arquivado'};
export const money = (value: string | number) => new Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL'}).format(Number(value));
export const dateLabel = (value: string) => new Date(value.slice(0, 10) + 'T12:00:00').toLocaleDateString('pt-BR');
export function Badge({status}: {status: Status}) {
  const color = status === 'REPROVADO' ? 'bg-red-50 text-red-700' : status === 'ASSINADO' || status === 'APROVADO' ? 'bg-emerald-50 text-emerald-700' : status === 'EM_ASSINATURA' ? 'bg-violet-50 text-violet-700' : 'bg-amber-50 text-amber-700';
  return <span className={`inline-flex rounded-md px-2.5 py-1 text-xs font-medium ${color}`}>{statusLabels[status]}</span>;
}
export function ErrorBanner({text}: {text: string}) {return text ? <p role="alert" className="my-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{text}</p> : null;}
export function Modal({title, close, children}: {title: string; close: () => void; children: ReactNode}) {
  return <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/40 p-4 backdrop-blur-sm" onKeyDown={e => {if(e.key === 'Escape') close();}}><section role="dialog" aria-modal="true" aria-label={title} className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"><div className="mb-6 flex items-center justify-between"><h2 className="text-xl font-semibold tracking-tight">{title}</h2><button className="icon-btn" aria-label="Fechar" onClick={close}><X size={20}/></button></div>{children}</section></div>;
}
