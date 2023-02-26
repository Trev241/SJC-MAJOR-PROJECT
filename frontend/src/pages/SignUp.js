import React from "react";
import Login from "./Login";
import { Link } from "react-router-dom"

export default function SignUp(){

    const handleClick = () => {

    }
    return(
        <>
            <h1>Sign Up</h1>
            <form onSubmit={handleClick}>
            <div className="input-group mb-3">
                    <div className="input-group-prepend">
                        <span className="input-group-text" id="name-label" >Name</span>
                    </div>
                    <input type="text" className="form-control" aria-describedby="name-label" />
               </div>
               <div className="input-group mb-3">
                    <div className="input-group-prepend">
                        <span className="input-group-text" id="email-label" >Email</span>
                    </div>
                    <input type="text" className="form-control" aria-describedby="email-label" />
               </div>
               <div className="input-group mb-3">
                    <div className="input-group-prepend">
                        <span className="input-group-text" id="confirm-email-label" >Confirm Email</span>
                    </div>
                    <input type="text" className="form-control" aria-describedby="confirm-email-label" />
                </div>
                <div className="input-group mb-3">
                    <div className="input-group-prepend">
                        <span className="input-group-text" id="password-label" >Password</span>
                    </div>
                    <input type="password" className="form-control" aria-describedby="password-label" />
                </div>
                <div className="input-group mb-3">
                    <div className="input-group-prepend">
                        <span className="input-group-text" id="confirm-password-label" >Confirm Password</span>
                    </div>
                    <input type="password" className="form-control" aria-describedby="confirm-password-label" />
                </div>
                <button type="button" class="btn btn-primary">Submit</button>

            </form>
        </>
    )
}