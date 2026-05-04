# Simulador DETRAN

Simulador de provas teóricas para habilitação no trânsito brasileiro, baseado em questões reais do DETRAN.

Acesse em: **[mpdepauladasilva.github.io/simulador-detran](https://mpdepauladasilva.github.io/simulador-detran/)**

---

## Funcionalidades

- **57 provas** com **1.589 questões** no total
- Categorias: Legislação, Direção Defensiva, Primeiros Socorros, Mecânica Básica, Meio Ambiente e Cidadania
- **Simulado DETRAN** com distribuição oficial de 30 questões por tema
- Feedback imediato ao errar, mostrando a alternativa correta
- Exibição de imagens de placas de trânsito nas questões que exigem
- Interface responsiva, funciona no celular e no computador

## Categorias de provas

| Categoria | Questões no simulado DETRAN |
|---|---|
| Legislação de Trânsito | 9 |
| Direção Defensiva | 9 |
| Primeiros Socorros | 4 |
| Mecânica Básica | 4 |
| Meio Ambiente e Cidadania | 4 |

## Como executar localmente

Não é necessário instalar nada. Basta clonar o repositório e abrir o `index.html` no navegador, ou rodar um servidor local:

```bash
git clone https://github.com/mpdepauladasilva/simulador-detran.git
cd simulador-detran
python3 parse_questions.py   # gera data/questions.json
python3 -m http.server 8000  # abre http://localhost:8000
```

## Estrutura do projeto

```
simulador-detran/
├── index.html              # interface principal
├── app.js                  # lógica do simulador
├── style.css               # estilos
├── parse_questions.py      # parser das provas → questions.json
├── download_images.py      # download automatizado de imagens de placas
├── data/
│   └── questions.json      # banco de questões gerado
├── images/                 # imagens das placas de trânsito
└── imagens_necessarias.csv # mapeamento de códigos de placas
```

## Tecnologias

- HTML, CSS e JavaScript puro (sem frameworks)
- Python 3 para processamento das provas
- GitHub Pages para hospedagem

## Licença

Este projeto está licenciado sob uso **não comercial**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
