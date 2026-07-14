console.log("Login JS Loaded");
document.getElementById("loginForm").addEventListener("submit", function(e){

    e.preventDefault();
    console.log("Login button clicked");
    fetch("/login",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({

            email:document.getElementById("email").value,

            password:document.getElementById("password").value

        })

    })

    .then(response=>response.json())

    .then(data=>{

        if(data.success){

            window.location.href="dashboard";

        }

        else{

            alert(data.message);

        }

    })

    .catch(error=>{

        console.log(error);

    });

});