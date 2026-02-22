import React from 'react';
import { NavLink } from 'react-router-dom';

export const Sidebar: React.FC = () => {
  const menuItems = [
    {
      path: '/',
      label: 'Dashboard',
      icon: '📊',
    },
    {
      path: '/empresas',
      label: 'Empresas',
      icon: '🏢',
    },
    {
      path: '/certificados',
      label: 'Certificados',
      icon: '🔐',
    },
    {
      path: '/cfops',
      label: 'CFOPs',
      icon: '📋',
    },
    {
      path: '/importacao',
      label: 'Importação',
      icon: '📁',
    },
    {
      path: '/classificacao',
      label: 'Classificação',
      icon: '🔄',
    },
    {
      path: '/relatorios',
      label: 'Relatórios',
      icon: '📈',
    },
    {
      path: '/logs',
      label: 'Logs',
      icon: '📝',
    },
    {
      path: '/configuracoes',
      label: 'Configurações',
      icon: '⚙️',
    },
  ];

  return (
    <nav className="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-title">DFE Sync</h1>
        <p className="sidebar-subtitle">Sistema de Gestão</p>
      </div>
      
      <ul className="sidebar-menu">
        {menuItems.map((item) => (
          <li key={item.path}>
            <NavLink 
              to={item.path}
              className={({ isActive }) => 
                `sidebar-item ${isActive ? 'active' : ''}`
              }
              end={item.path === '/'}
            >
              <span className="sidebar-item-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
};