# Acesso pela rede da empresa

Status atual: a aplicação roda via Docker nesta máquina e já é acessível por
qualquer pessoa na mesma rede, usando IP:porta — não precisa de nenhuma
configuração adicional pra isso funcionar. O que falta, opcionalmente, é um
nome amigável no lugar do IP puro.

## Dados desta máquina

- Nome do computador: `PC-SQUAD-01`
- IPs na rede local: Wi-Fi `192.168.1.51` · Ethernet `192.168.1.50`
- Porta da aplicação: `8000` (definida em `docker-compose.yml`)

Qual IP é o certo depende de qual interface está de fato ligada à rede da
empresa. Pra descobrir: um colega tenta acessar os dois endereços abaixo e vê
qual responde.

- `http://192.168.1.51:8000`
- `http://192.168.1.50:8000`

## Opções de nome, do mais simples ao mais robusto

**1. Nome do computador via NetBIOS (grátis, sem configurar nada)**
Em rede Windows, o nome da máquina costuma resolver sozinho.
Testar: `http://PC-SQUAD-01:8000`

**2. Nome customizado via `hosts` file (feito na mão, por máquina)**
Cada colega edita (como admin) `C:\Windows\System32\drivers\etc\hosts` e
adiciona uma linha:
```
192.168.1.50  registro.local
```
Depois acessa por `http://registro.local:8000`. Manual por pessoa, e quebra
se o IP desta máquina mudar — por isso, se for usar essa opção, vale pedir
pro TI reservar um IP fixo (DHCP reservation) pra essa máquina antes.

**3. DNS interno da empresa (a opção que escala)**
Pedir pro time de TI/infra cadastrar um registro A ou CNAME (ex.:
`registro.empresa.local`) apontando pro IP fixo desta máquina, no DNS
interno da empresa. É a única opção que não depende de configurar cada PC
manualmente, mas exige alguém com acesso ao DNS — não é algo que dá pra
fazer só por aqui.

## Decisão

Por enquanto, ficamos no acesso direto por IP (sem nome amigável). Revisitar
quando fizer sentido — provavelmente quando/se a aplicação for pra um
servidor fixo da empresa em vez desta máquina.
