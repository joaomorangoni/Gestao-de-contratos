import {useId, useState} from 'react';
import {FileSearch, LoaderCircle, Sparkles, UploadCloud} from 'lucide-react';
import {api, message} from '../api';
import {ErrorBanner} from '../ui';

export interface ProposalExtraction {
  nome_fornecedor: string;
  cnpj_fornecedor: string | null;
  valor_total: number;
  prazo_vigencia_meses: number;
  objeto_resumido: string;
}
export interface RiskAnalysis {
  nivel_risco_geral: 'Baixo' | 'Médio' | 'Alto';
  clausulas_atencao: {clausula: string; motivo_risco: string; sugestao_correcao: string}[];
}
type Props = {mode: 'proposal'; onExtracted: (data: ProposalExtraction) => void; onBusyChange?: (busy: boolean) => void}
  | {mode: 'risk'; onBusyChange?: (busy: boolean) => void};

export default function AIContractUploader(props: Props) {
  const id = useId();
  const [file, setFile] = useState<File | null>(null), [text, setText] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [risk, setRisk] = useState<RiskAnalysis | null>(null), [success, setSuccess] = useState(false);
  function selectFile(selected?: File) {
    setError(''); setRisk(null); setSuccess(false); setFile(null);
    if (!selected) return;
    if (!selected.name.toLowerCase().endsWith('.pdf') || selected.size === 0 || selected.size > 5 * 1024 * 1024) {
      setError('Selecione um PDF válido de até 5 MB.'); return;
    }
    setText(''); setFile(selected);
  }
  async function process() {
    if (busy || (!file && !text.trim())) return;
    setBusy(true); props.onBusyChange?.(true); setError(''); setRisk(null); setSuccess(false);
    const form = new FormData(); if (file) form.append('file', file);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 75000);
    try {
      if (props.mode === 'proposal') {
        const data = await api<ProposalExtraction>('/ai/extrair-proposta', {method: 'POST', body: form, signal: controller.signal});
        props.onExtracted(data); setSuccess(true);
      } else {
        setRisk(await api<RiskAnalysis>('/ai/analisar-riscos', {
          method: 'POST', body: file ? form : JSON.stringify({text}), signal: controller.signal,
        }));
      }
    } catch (e) {setError(controller.signal.aborted ? 'Tempo de processamento excedido. Tente novamente com um documento menor.' : message(e));}
    finally {clearTimeout(timer); setBusy(false); props.onBusyChange?.(false);}
  }
  return <section className="space-y-4 rounded-xl border border-emerald-200 bg-emerald-50/30 p-4" aria-busy={busy}>
    <div className="flex items-center gap-2 text-sm font-semibold text-emerald-700"><Sparkles size={18}/>{props.mode === 'proposal' ? 'Preencher com uma proposta' : 'Auditoria de compliance e riscos'}</div>
    <p className="text-xs leading-5 text-slate-500">{props.mode === 'proposal' ? 'Extraia fornecedor, CNPJ, valor, objeto e vigência. Revise as sugestões antes de enviar o pedido.' : 'Identifique cláusulas que merecem atenção e sugestões para revisão jurídica.'} Ao processar, o conteúdo é enviado ao Google Gemini.</p>
    <div onDragOver={e => e.preventDefault()} onDrop={e => {e.preventDefault(); if (!busy) selectFile(e.dataTransfer.files[0]);}} className="rounded-lg border border-dashed border-emerald-200 p-4">
      <label htmlFor={id} className="flex items-center gap-2"><UploadCloud size={18}/>{file ? file.name : 'Arraste um PDF ou selecione o arquivo'}</label>
      <input id={id} type="file" accept=".pdf,application/pdf" disabled={busy} onChange={e => {selectFile(e.target.files?.[0]); e.currentTarget.value = '';}}/>
      <p className="mt-2 text-[10px] text-slate-400">Até 5 MB e 100 páginas. PDFs protegidos por senha não são aceitos.</p>
      {file && <button type="button" className="mt-2 text-xs text-slate-500 underline" disabled={busy} onClick={() => {setFile(null); setRisk(null); setSuccess(false);}}>Remover seleção</button>}
    </div>
    {props.mode === 'risk' && !file && <label>Ou cole o texto da minuta<textarea rows={4} maxLength={60000} value={text} disabled={busy} onChange={e => {setText(e.target.value); setRisk(null);}} placeholder="Cole o conteúdo do contrato para análise…"/></label>}
    <button type="button" className="btn-primary" disabled={busy || (!file && !text.trim())} onClick={() => void process()}>{busy ? <LoaderCircle size={16} className="animate-spin"/> : <FileSearch size={16}/>}Processar com IA</button>
    {busy && <p role="status" className="text-xs text-emerald-700">Analisando documento com Inteligência Artificial...</p>}
    <ErrorBanner text={error}/>
    {success && <p role="status" className="text-xs text-emerald-700">Campos preenchidos. Confira os dados; o PDF usado pela IA deve ser incluído nos anexos se desejar salvá-lo.</p>}
    {risk && <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-2"><h4 className="text-sm font-semibold">Resultado da análise</h4><span className={`rounded-md px-3 py-1 text-xs font-semibold ${risk.nivel_risco_geral === 'Alto' ? 'bg-red-50 text-red-700' : risk.nivel_risco_geral === 'Médio' ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'}`}>Risco {risk.nivel_risco_geral}</span></div>
      {!risk.clausulas_atencao.length && <p className="text-xs text-slate-500">Nenhuma cláusula sinalizada nesta análise. Isso não garante ausência de riscos.</p>}
      {risk.clausulas_atencao.map((clause, index) => <details key={index} className="rounded-lg border border-slate-200 p-3"><summary className="cursor-pointer whitespace-pre-wrap text-xs font-semibold">{clause.clausula}</summary><div className="mt-3 space-y-3 text-xs leading-6 text-slate-600"><div><b>Motivo do risco</b><p className="whitespace-pre-wrap">{clause.motivo_risco}</p></div><div><b>Sugestão de correção</b><p className="whitespace-pre-wrap">{clause.sugestao_correcao}</p></div></div></details>)}
      <p className="text-[10px] leading-5 text-slate-400">Análise auxiliar gerada por IA, sujeita a erros. Exige revisão jurídica humana e não altera aprovações nem o contrato. O resultado não é salvo automaticamente.</p>
    </div>}
  </section>;
}
