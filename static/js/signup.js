document.getElementById("signupForm").addEventListener("submit", async function(e){

    e.preventDefault();   // prevents page reload

    let name = document.getElementById("name").value;
    let email = document.getElementById("email").value;
    let phone = document.getElementById("phone").value;
    let password = document.getElementById("password").value;
    let confirmPassword = document.getElementById("confirmPassword").value;
    let role = document.getElementById("role").value;


    if(password !== confirmPassword){
        alert("Passwords do not match");
        return;
    }


    if(role === ""){
        alert("Please select a role");
        return;
    }


    let response = await fetch("/signup", {

        method: "POST",

        headers:{
            "Content-Type":"application/json"
        },

        body: JSON.stringify({

            name: name,
            email: email,
            phone: phone,
            password: password,
            role: role

        })

    });


    let data = await response.json();


    if(data.success){

        alert("Account created successfully");

        window.location.href="/";

    }
    else{

        alert(data.message);

    }


});