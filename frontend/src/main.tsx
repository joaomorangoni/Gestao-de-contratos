import {createRoot} from 'react-dom/client';
import App from './App';
import './tailwind.css';
import './theme.css';
import ThemeToggle from './components/ThemeToggle';

createRoot(document.getElementById('root')!).render(<><App/><ThemeToggle/></>);
