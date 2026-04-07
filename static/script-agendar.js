formAgendamento.addEventListener("submit", async function(event) {
    event.preventDefault();

    const nome = document.getElementById("nome").value.trim();
    const telefone = document.getElementById("telefone").value.trim();
    const servico = document.getElementById("servico").value;
    const data = document.getElementById("inicio").value;
    const dataObj = new Date(data);
    
    const ano = dataObj.getFullYear();

    if(nome === "" || telefone === "" || servico === "" || data === ""){
        Swal.fire({
            title: "Erro!",
            text: "Todos os campos devem ser preenchidos!",
            icon: "error"
        });
        return;
    }

    if (isNaN(dataObj)) {
        Swal.fire({
            title: "Erro!",
            text: "Data inválida!",
            icon: "error"
        });
        return;
    }

    if (ano < 2026 || ano > 2100) {
        Swal.fire({
            title: "Erro!",
            text: "Ano inválido!",
            icon: "error"
        });
        return;
    }

    // Eu pego o resultado do teste em python, ai continuo com os botões 
    const formData = new FormData(formAgendamento);

    const response = await fetch("/agendar", {
        method: "POST",
        body: formData
    });

    const dataResponse = await response.json();

    if (dataResponse.mensagem === "Agendamento criado com sucesso!") {
        Swal.fire({
            title: "Sucesso!",
            text: dataResponse.mensagem,
            icon: "success"
        });
    } else {
        Swal.fire({
            title: "Erro!",
            text: dataResponse.mensagem,
            icon: "error"
        });
    }
});