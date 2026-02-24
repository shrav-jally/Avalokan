import React, { useState } from 'react';
import {
    LayoutDashboard,
    FileText,
    Globe,
    ChevronLeft,
    ChevronRight,
    Menu,
    Home,
    FileEdit
} from 'lucide-react';

const Sidebar = ({ activeTab, onTabChange }) => {
    const [isCollapsed, setIsCollapsed] = useState(false);

    const navItems = [
        { label: 'Home', id: 'home', icon: Home },
        { label: 'Dashboard', id: 'dashboard', icon: LayoutDashboard },
        { label: 'Policies', id: 'policies', icon: FileText },
        { label: 'Draft Management', id: 'draftManagement', icon: FileEdit },
        { label: 'Global Engagement', id: 'global', icon: Globe }
    ];

    return (
        <aside className={`left-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
            <div className="sidebar-brand" style={{ justifyContent: isCollapsed ? 'center' : 'flex-end' }}>
                <button
                    className="collapse-toggle"
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                >
                    {isCollapsed ? <Menu size={20} /> : <ChevronLeft size={20} />}
                </button>
            </div>

            <nav className="sidebar-nav">
                <ul>
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        return (
                            <li
                                key={item.id}
                                className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                                onClick={() => onTabChange(item.id)}
                            >
                                <div className="nav-item-content">
                                    <Icon size={20} className="nav-icon" />
                                    {!isCollapsed && <span className="nav-label">{item.label}</span>}
                                </div>
                            </li>
                        );
                    })}
                </ul>
            </nav>

            <div className="sidebar-footer">
                {!isCollapsed ? (
                    <>
                        <p>© 2026 Admin Panel</p>
                        <p>V1.2.4-STABLE</p>
                    </>
                ) : (
                    <p className="footer-mini">v1.2</p>
                )}
            </div>
        </aside>
    );
};

export default Sidebar;
