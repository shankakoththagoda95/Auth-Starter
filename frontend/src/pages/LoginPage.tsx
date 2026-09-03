import { zodResolver } from "@hookform/resolvers/zod";
import { useState, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { z } from "zod";
import { ApiError } from "../api";
import { useAuth } from "../auth";

const schema = z.object({ identifier: z.string().min(3, "Enter your email or username."), password: z.string().min(1, "Enter your password.") });
type Values = z.infer<typeof schema>;
export function LoginPage() { const { user, login } = useAuth(); const navigate = useNavigate(); const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Values>({ resolver: zodResolver(schema) }); const [error, setError] = useState<string | null>(null); if (user) return <Navigate to="/account" replace />; async function submit(values: Values) { setError(null); try { await login(values.identifier, values.password); navigate("/account"); } catch (caught) { setError(caught instanceof ApiError ? caught.message : "Unable to sign in."); } } return <section className="form-wrap"><p className="eyebrow">WELCOME BACK</p><h1>Sign in.</h1><form onSubmit={handleSubmit(submit)} noValidate><Field label="Email or username" error={errors.identifier?.message}><input autoComplete="username" {...register("identifier")} /></Field><Field label="Password" error={errors.password?.message}><input autoComplete="current-password" type="password" {...register("password")} /></Field>{error && <p className="form-error">{error}</p>}<button className="button" disabled={isSubmitting} type="submit">{isSubmitting ? "Signing in…" : "Sign in"}</button></form><p className="form-footer"><Link to="/reset-password">Forgot password?</Link><br />New here? <Link to="/register">Create an account</Link></p></section>; }
function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) { return <label className="field"><span>{label}</span>{children}{error && <small className="field-error">{error}</small>}</label>; }
