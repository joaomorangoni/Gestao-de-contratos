import {useState} from 'react';
import type {FormEvent} from 'react';
import {UploadCloud, Send} from 'lucide-react';
import {api, message} from '../api';
import {ErrorBanner} from '../ui';

export default function RequestForm({onCreated}: {onCreated: () => void}) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError('');
    const data = new FormData(event.currentTarget);
    const files = data.getAll('attachments').filter((file): file is File => file instanceof File && file.size > 0);
    if (files.length > 5 || files.some(file => file.size > 5 * 1024 * 1024)) {setError('Envie até cinco arquivos, com no máximo 5 MB cada.'); return;}
    data.delete('attachments'); files.forEach(file => data.append('attachments', file));
    setBusy(true);
    try {await api('/requests', {method:'POST', body:data}); onCreated();} catch (e) {setError(message(e));} finally {setBusy(false);}
  }
  return <form onSubmit={submit} className="space-y-6">
    <p className="text-sm text-slate-500">Conte o que precisa contratar. Seu pedido seguirá para Financeiro, Jurídico e Compliance.</p>
    <fieldset disabled={busy} className="space-y-6">
      <section><h3 className="section-label">01 · Sobre a contratação</h3><div className="grid gap-4 md:grid-cols-2">
        <label className="md:col-span-2">Objeto do contrato *<input name="subject" required maxLength={200} placeholder="Ex.: Licenciamento anual de software"/></label>
        <label className="md:col-span-2">Escopo / descrição *<textarea name="description" required maxLength={10000} rows={3} placeholder="Descreva as entregas, condições e necessidades da contratação."/></label>
        <label>Valor total (R$) *<input name="amount" type="number" min="0" max="9999999999.99" step="0.01" required placeholder="0,00"/></label>
        <label>Centro de custo *<input name="cost_center" required maxLength={100} placeholder="Ex.: TI — Operações"/></label>
      </div></section>
      <section><h3 className="section-label">02 · Dados do fornecedor</h3><div className="grid gap-4 md:grid-cols-2">
        <label className="md:col-span-2">Nome / razão social *<input name="supplier_name" required maxLength={150} placeholder="Nome do fornecedor"/></label>
        <label>CPF / CNPJ *<input name="supplier_document" required maxLength={30} placeholder="Documento do fornecedor"/></label>
        <label>E-mail para assinatura *<input name="supplier_email" type="email" required maxLength={254} placeholder="contato@empresa.com.br"/></label>
      </div></section>
      <section><h3 className="section-label">03 · Proposta e escopo</h3><label className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-emerald-200 bg-emerald-50/30 p-6 text-center"><UploadCloud className="text-emerald-600"/><span>Selecione os anexos da solicitação</span><span className="text-xs text-slate-400">PDF ou TXT · Até 5 arquivos de 5 MB · Opcional</span><input className="max-w-full text-xs" name="attachments" type="file" accept=".pdf,.txt" multiple/></label></section>
      <ErrorBanner text={error}/><div className="flex justify-end border-t border-slate-100 pt-5"><button className="btn-primary" type="submit" disabled={busy}><Send size={16}/>{busy ? 'Enviando…' : 'Enviar para aprovação'}</button></div>
    </fieldset>
  </form>;
}
