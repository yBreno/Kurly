const formAgendamento = document.getElementById("agendamento");

formAgendamento.addEventListener("submit", function(event) {
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
            icon: "error",
            background: "#0f0f1a",
            color: "#fff",
            confirmButtonColor: "#7c3aed"
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

    if (ano < 2024 || ano > 2100) {
        Swal.fire({
            title: "Erro!",
            text: "Ano inválido!",
            icon: "error"
        });
        return;
    }

    Swal.fire({
        title: "Sucesso!",
        text: "Agendamento criado!",
        icon: "success",
        background: "#0f0f1a",
        color: "#fff",
        confirmButtonColor: "#7c3aed"
    }).then(() => {
        formAgendamento.submit(); 
    });
});