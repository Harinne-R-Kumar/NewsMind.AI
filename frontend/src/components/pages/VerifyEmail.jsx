import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { authAPI } from "../../services/api";

export default function VerifyEmail() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    const [message, setMessage] = useState("Verifying your email...");

    useEffect(() => {
        async function verify() {
            try {
                const token = searchParams.get("token");

                if (!token) {
                    setMessage("Invalid verification link.");
                    return;
                }

                await authAPI.verifyEmail(token);

                setMessage("✅ Email verified successfully!");

                setTimeout(() => {
                    navigate("/login");
                }, 2500);

            } catch (err) {
                console.error(err);
                setMessage("❌ Verification failed.");
            }
        }

        verify();
    }, []);

    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center">
            <div className="bg-slate-900 p-8 rounded-xl text-center">
                <h1 className="text-2xl font-bold text-white">
                    {message}
                </h1>
            </div>
        </div>
    );
}