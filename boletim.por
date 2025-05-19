programa {
  funcao inicio() {
  //variaveis
  real n1, n2, media 
  //Ler da tela as duas notas 
  escreva("digite a nota da prova: ")
  leia(n1)
  escreva(" digite nota dois: ")
  leia(n2) 
  //Cálculo da média
  media=(n1+n2)/2
  escreva("Média é",media)
  //comando condicional
  se(media >=6){
  escreva("\nAprovado - PD")
  }senao{
  escreva("\nReprovado")
  }
  }
}
