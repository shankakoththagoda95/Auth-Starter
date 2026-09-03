import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export function AccountPage() { const { user, loading, logout } = useAuth(); const navigate = useNavigate(); if (loading) return <p className="loading">Loading your account…</p>; if (!user) return <Navigate to="/login" replace />; async function signOut() { await logout(); navigate("/"); } return <section className="account-card"><p className="eyebrow">YOUR ACCOUNT</p><h1>Hello, {user.username}.</h1><dl><div><dt>Email</dt><dd>{user.email}</dd></div><div><dt>Status</dt><dd><span className="verified">Verified</span></dd></div></dl><button className="button button-secondary" onClick={() => void signOut()} type="button">Sign out</button></section>; }
