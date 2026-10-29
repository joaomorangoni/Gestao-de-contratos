import {useState} from 'react';
import type {FormEvent} from 'react';
import {UploadCloud, Send} from 'lucide-react';
import {api, message} from '../api';
import {ErrorBanner} from '../ui';
import AIContractUploader from './AIContractUploader';
import type {ProposalExtraction} from './AIContractUploader';

export default function RequestForm({onCreated}: {onCreated: () => void}) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [aiBusy, setAiBusy] = useState(false);
  const [draft, setDraft] = useState({subject:'', description:'', amount:'', supplier_name:'', supplier_document:''});
  function applyProposal(data: ProposalExtraction) {
    setDraft({subject:data.objeto_resumido, description:`${data.objeto_resumido}\nPrazo de vigência da proposta: ${data.prazo_vigencia_meses} meses.`,
      amount:data.valor_total.toFixed(2), supplier_name:data.nome_fornecedor, supplier_document:data.cnpj_fornecedor ?? ''});
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (aiBusy) return; setError('');
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
      <AIContractUploader mode="proposal" onExtracted={applyProposal} onBusyChange={setAiBusy}/>
      <section><h3 className="section-label">01 · Sobre a contratação</h3><div className="grid gap-4 md:grid-cols-2">
        <label className="md:col-span-2">Objeto do contrato *<input name="subject" value={draft.subject} onChange={e => setDraft({...draft, subject: e.target.value})} disabled={aiBusy} required maxLength={200} placeholder="Ex.: Licenciamento anual de software"/></label>
        <label className="md:col-span-2">Escopo / descrição *<textarea name="description" value={draft.description} onChange={e => setDraft({...draft, description: e.target.value})} disabled={aiBusy} required maxLength={10000} rows={3} placeholder="Descreva as entregas, condições e necessidades da contratação."/></label>
        <label>Valor total (R$) *<input name="amount" value={draft.amount} onChange={e => setDraft({...draft, amount: e.target.value})} disabled={aiBusy} type="number" min="0" max="9999999999.99" step="0.01" required placeholder="0,00"/></label>
        <label>Centro de custo *<input name="cost_center" required maxLength={100} placeholder="Ex.: TI — Operações"/></label>
      </div></section>
      <section><h3 className="section-label">02 · Dados do fornecedor</h3><div className="grid gap-4 md:grid-cols-2">
        <label className="md:col-span-2">Nome / razão social *<input name="supplier_name" value={draft.supplier_name} onChange={e => setDraft({...draft, supplier_name: e.target.value})} disabled={aiBusy} required maxLength={150} placeholder="Nome do fornecedor"/></label>
        <label>CPF / CNPJ *<input name="supplier_document" value={draft.supplier_document} onChange={e => setDraft({...draft, supplier_document: e.target.value})} disabled={aiBusy} required maxLength={30} placeholder="Documento do fornecedor"/></label>
        <label>E-mail para assinatura *<input name="supplier_email" type="email" required maxLength={254} placeholder="contato@empresa.com.br"/></label>
      </div></section>
      <section><h3 className="section-label">03 · Proposta e escopo</h3><label className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-emerald-200 bg-emerald-50/30 p-6 text-center"><UploadCloud className="text-emerald-600"/><span>Selecione os anexos da solicitação</span><span className="text-xs text-slate-400">PDF ou TXT · Até 5 arquivos de 5 MB · Opcional</span><input className="max-w-full text-xs" name="attachments" type="file" accept=".pdf,.txt" multiple/></label></section>
      <ErrorBanner text={error}/><div className="flex justify-end border-t border-slate-100 pt-5"><button className="btn-primary" type="submit" disabled={busy || aiBusy}><Send size={16}/>{busy ? 'Enviando…' : 'Enviar para aprovação'}</button></div>
    </fieldset>
  </form>;
}
