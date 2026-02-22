import { type ReactNode, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router";

import { useAuthStore } from "@/stores/auth";

import styles from "./AppShell.module.css";

export function AppShell({ children }: { children: ReactNode }) {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const toggleLang = () => {
    const next = i18n.language === "pt-BR" ? "en" : "pt-BR";
    i18n.changeLanguage(next);
  };

  const navLinkClass = (path: string) =>
    location.pathname.startsWith(path) ? styles.active : "";

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Link to="/" className={styles.logo}>
          {t("app.title")}
        </Link>
        <button
          className={styles.hamburger}
          onClick={() => setMenuOpen((prev) => !prev)}
          aria-label="Menu"
        >
          &#9776;
        </button>
        <nav className={`${styles.nav} ${menuOpen ? styles.navOpen : ""}`}>
          <Link
            to="/search"
            className={navLinkClass("/search")}
            onClick={() => setMenuOpen(false)}
          >
            {t("nav.search")}
          </Link>
          <Link
            to="/patterns"
            className={navLinkClass("/patterns")}
            onClick={() => setMenuOpen(false)}
          >
            {t("nav.patterns")}
          </Link>
          <Link
            to="/baseline"
            className={navLinkClass("/baseline")}
            onClick={() => setMenuOpen(false)}
          >
            {t("nav.baseline")}
          </Link>
          <Link
            to="/investigations"
            className={navLinkClass("/investigations")}
            onClick={() => setMenuOpen(false)}
          >
            {t("nav.investigations")}
          </Link>
        </nav>
        <div className={styles.headerActions}>
          {token ? (
            <div className={styles.userArea}>
              {user && <span className={styles.userEmail}>{user.email}</span>}
              <button onClick={handleLogout} className={styles.authBtn}>
                {t("nav.logout")}
              </button>
            </div>
          ) : (
            <Link to="/login" className={styles.authBtn}>
              {t("nav.login")}
            </Link>
          )}
          <button onClick={toggleLang} className={styles.langToggle}>
            {i18n.language === "pt-BR" ? "EN" : "PT"}
          </button>
        </div>
      </header>
      <main className={styles.main}>{children}</main>
      <footer className={styles.footer}>
        <span className={styles.disclaimer}>{t("app.disclaimer")}</span>
      </footer>
    </div>
  );
}
