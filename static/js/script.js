const tbody = document.querySelector("#wordsTable tbody");

// ===========================================
// Add Row
// ===========================================

document.getElementById("addRow").onclick = function(){

    let row = document.createElement("tr");

    row.innerHTML = `
    <td>
        <input type="text" class="form-control word">
    </td>

    <td>
        <input type="text" class="form-control arabic">
    </td>

    <td>
        <input type="file" class="form-control image">
    </td>

    <td>
        <button type="button" class="btn btn-danger deleteRow">
            Delete
        </button>
    </td>
    `;

    tbody.appendChild(row);

};

// ===========================================
// Delete Row
// ===========================================

document.addEventListener("click", function(e){

    if(e.target.classList.contains("deleteRow")){

        if(tbody.rows.length>1){

            e.target.closest("tr").remove();

        }

    }

});

// ===========================================
// Generate
// ===========================================

document.getElementById("generate").onclick = async function(){

    const btn = document.getElementById("generate");

    btn.disabled = true;
    btn.innerHTML = "Generating...";

    let formData = new FormData();

    formData.append(
        "signature",
        document.getElementById("signature").value
    );

    formData.append(
        "academy",
        document.getElementById("academy").value
    );

    formData.append(
        "voice",
        document.getElementById("voice").value
    );

    formData.append(
        "speed",
        document.getElementById("speed").value
    );

    let logo=document.getElementById("logo").files[0];

    if(logo){

        formData.append(
            "logo",
            logo
        );

    }

    let rows=document.querySelectorAll("#wordsTable tbody tr");

    rows.forEach((row,index)=>{

        formData.append(
            `word_${index}`,
            row.querySelector(".word").value
        );

        formData.append(
            `arabic_${index}`,
            row.querySelector(".arabic").value
        );

        let img=row.querySelector(".image").files[0];

        if(img){

            formData.append(
                `image_${index}`,
                img
            );

        }

    });

    formData.append(
        "count",
        rows.length
    );

    const progressBox = document.getElementById("progressBox");
    const progressBar = document.getElementById("progressBar");

    progressBox.style.display = "block";

    progressBar.style.width = "10%";
    progressBar.innerHTML = "Preparing...";

    let response=await fetch(
        "/generate",
        {
            method:"POST",
            body:formData
        }
    );

    progressBar.style.width = "40%";
    progressBar.innerHTML = "Generating Audio...";

    let result=await response.json();

    progressBar.style.width = "90%";
    progressBar.innerHTML = "Finalizing...";

    progressBar.style.width = "100%";
    progressBar.innerHTML = "Completed ✓";

    setTimeout(() => {
        progressBox.style.display = "none";
        progressBar.style.width = "0%";
    }, 1000);

    alert(result.message);

    btn.disabled = false;
    btn.innerHTML = "🎬 Generate Video";
    
    window.location.href = "/download";

};
