import {useState} from 'react';
import {Moon, Sun} from 'lucide-react';

type Theme = 'dark' | 'light';

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => document.documentElement.dataset.theme === 'light' ? 'light' : 'dark');

  function toggle() {
    const next = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    setTheme(next);
    try { localStorage.setItem('accordo-theme', next); } catch { /* Mantém a escolha durante esta visita. */ }
  }

  return <button type="button" className="theme-toggle" onClick={toggle}
    aria-label={theme === 'dark' ? 'Ativar modo claro' : 'Ativar modo escuro'}
    title={theme === 'dark' ? 'Ativar modo claro' : 'Ativar modo escuro'}>
    {theme === 'dark' ? <Sun size={17}/> : <Moon size={17}/>}
    <span>{theme === 'dark' ? 'Modo claro' : 'Modo escuro'}</span>
  </button>;
}
