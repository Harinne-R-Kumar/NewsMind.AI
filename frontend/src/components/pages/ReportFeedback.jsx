import { useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";

export default function ReportFeedback() {

    const { reportId } = useParams();

    const [feedback, setFeedback] = useState("");

    async function submitFeedback() {

        try {
    
            const token = localStorage.getItem("token");
    
            const response = await axios.post(
    
                `http://localhost:8000/api/feedback/report/${reportId}`,
    
                {
                    improvement_request: feedback
                },
    
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
    
            );
    
            alert("Thank you!");
    
            console.log(response.data);
    
        }
        catch(err){
    
            console.log(err.response);
    
            alert("Failed to submit feedback.");
    
        }
    
    }

    return (
        <div>

            <h2>Thank you for your rating.</h2>

            <h3>What can we improve?</h3>

            <textarea

                rows={6}

                value={feedback}

                onChange={(e)=>setFeedback(e.target.value)}

            />

            <br/>

            <button onClick={submitFeedback}>
                Submit
            </button>

        </div>
    );
}