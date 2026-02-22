import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Empresas } from './pages/Cadastros/Empresas';
import Certificados from './pages/Cadastros/Certificados';
import { CFOPs } from './pages/Cadastros/CFOPs';
import { Importacao } from './pages/Importacao/Importacao';
import { Classificacao } from './pages/Classificacao/Classificacao';
import { Relatorios } from './pages/Relatorios/Relatorios';
import { Logs } from './pages/Relatorios/Logs';
import { Configuracoes } from './pages/Configuracoes/Configuracoes';
import { XMLViewer } from './pages/Classificacao/XMLViewer';
import './App.css';

export const App: React.FC = () => {
  return (
    <Router future={{ v7_startTransition: true }}>
      <Layout>
        <Routes>
          {/* Dashboard */}
          <Route path="/" element={<Dashboard />} />
          
          {/* Cadastros */}
          <Route path="/empresas" element={<Empresas />} />
          <Route path="/certificados" element={<Certificados />} />
          <Route path="/cfops" element={<CFOPs />} />
          
          {/* Importação */}
          <Route path="/importacao" element={<Importacao />} />
          
          {/* Classificação */}
          <Route path="/classificacao" element={<Classificacao />} />
          <Route path="/xml-viewer/:id" element={<XMLViewer />} />
          
          {/* Relatórios */}
          <Route path="/relatorios" element={<Relatorios />} />
          <Route path="/logs" element={<Logs />} />
          
          {/* Configurações */}
          <Route path="/configuracoes" element={<Configuracoes />} />
        </Routes>
      </Layout>
    </Router>
  );
};