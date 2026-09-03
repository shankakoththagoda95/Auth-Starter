import { Link, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import { AccountPage } from "./pages/AccountPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";

function Layout() { const { user, loading } = useAuth(); return <div className="site-shell"><header className="site-header"><Link className="brand" to="/">AUTHBASE</Link><nav>{loading ? null : user ? <Link to="/account">Account</Link> : <><Link to="/login">Sign in</Link><Link className="nav-cta" to="/register">Create account</Link></>}</nav></header><main className="page-content"><Routes><Route path="/" element={<Home />} /><Route path="/register" element={<RegisterPage />} /><Route path="/verify-email" element={<VerifyEmailPage />} /><Route path="/login" element={<LoginPage />} /><Route path="/reset-password" element={<ResetPasswordPage />} /><Route path="/account" element={<AccountPage />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></main></div>; }
function Home() { const { user } = useAuth(); return <section className="hero"><p className="eyebrow">REUSABLE AUTHENTICATION</p><h1>Start every product with a secure account system.</h1><p className="lede">Email verification, protected sessions, and a foundation designed to grow with your next idea.</p><div className="actions"><Link className="button" to={user ? "/account" : "/register"}>{user ? "Open account" : "Create account"}</Link><Link className="button button-secondary" to="/login">Sign in</Link></div></section>; }
export function App() { return <AuthProvider><Layout /></AuthProvider>; }
