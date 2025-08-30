# 🤝 Guia de Contribuição - PitchAI

## 📋 Visão Geral

Este guia explica como contribuir efetivamente para o PitchAI, especialmente quando 2-4 desenvolvedores estão trabalhando simultaneamente no projeto.

---

## 🌳 Estratégia de Branches

### **Branch Principal**
- `main` - Branch de produção, sempre estável
- Só aceita merges via Pull Request
- Protegida contra push direto

### **Branches de Desenvolvimento**
```
main
├── develop                    # Branch de integração
├── feature/frontend-start     # Tela inicial
├── feature/frontend-analysis  # Tela de análise  
├── feature/backend-npu       # Integração NPU
├── feature/audio-capture     # Captura de áudio
├── hotfix/ui-responsive      # Correções urgentes
└── docs/setup-guide          # Documentação
```

### **Convenção de Nomes**
- `feature/nome-da-feature` - Novas funcionalidades
- `fix/nome-do-bug` - Correções de bugs
- `hotfix/urgente` - Correções críticas
- `docs/nome-da-doc` - Documentação
- `refactor/nome-refactor` - Refatorações

---

## 🔄 Workflow de Desenvolvimento

### **1. Setup Inicial**
```bash
# Clone do repositório
git clone https://github.com/seu-usuario/PitchAI.git
cd PitchAI

# Ativar ambiente virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

### **2. Começar Nova Feature**
```bash
# Atualizar main
git checkout main
git pull origin main

# Criar nova branch
git checkout -b feature/minha-feature

# Fazer commit inicial
git commit --allow-empty -m "feat: iniciar feature minha-feature"
git push -u origin feature/minha-feature
```

### **3. Desenvolvimento**
```bash
# Commits frequentes e descritivos
git add .
git commit -m "feat(ui): adicionar StartWidget com glassmorphism"
git push

# Atualizar com main periodicamente
git checkout main
git pull
git checkout feature/minha-feature
git rebase main
```

### **4. Pull Request**
1. Push final da branch
2. Abrir PR no GitHub
3. Preencher template de PR
4. Aguardar review de pelo menos 1 colega
5. Mergear após aprovação

---

## 📝 Convenção de Commits

Seguimos o padrão **Conventional Commits**:

```
<tipo>(escopo): <descrição>

[corpo opcional]

[rodapé opcional]
```

### **Tipos**
- `feat` - Nova funcionalidade
- `fix` - Correção de bug
- `docs` - Documentação
- `style` - Formatação (não afeta código)
- `refactor` - Refatoração de código
- `test` - Testes
- `chore` - Tarefas de build/config

### **Exemplos**
```bash
feat(ui): adicionar tela inicial com botão start
fix(audio): corrigir captura de áudio no Windows
docs(readme): atualizar instruções de instalação
style(main): ajustar espaçamento dos widgets
refactor(npu): reorganizar classes do manager
test(audio): adicionar testes de captura
chore(deps): atualizar PyQt6 para v6.6.0
```

---

## 👥 Divisão de Trabalho

### **Por Desenvolvedor**

#### **Dev 1 - Frontend Core**
- `feature/frontend-start` - Tela inicial
- `feature/frontend-analysis` - Tela de análise
- `feature/frontend-summary` - Tela de resumo
- `feature/ui-responsive` - Responsividade

#### **Dev 2 - Backend NPU**
- `feature/backend-npu` - Manager NPU
- `feature/ai-whisper` - Transcrição
- `feature/ai-sentiment` - Análise sentimento
- `feature/ai-objections` - Detecção objeções

#### **Dev 3 - Audio & Data**
- `feature/audio-capture` - Captura áudio
- `feature/audio-processing` - Processamento
- `feature/database` - Banco SQLite
- `feature/data-models` - Modelos dados

#### **Dev 4 - Integration & DevOps**
- `feature/integration` - Integração sistemas
- `feature/deployment` - Scripts deploy
- `docs/setup-guide` - Documentação
- `feature/testing` - Suite testes

### **Por Módulo**
```
src/
├── ui/          → Dev 1 (Frontend)
├── ai/          → Dev 2 (Backend NPU)  
├── audio/       → Dev 3 (Audio)
├── core/        → Dev 4 (Integration)
└── data/        → Dev 3 (Data)
```

---

## 🔧 Resolução de Conflitos

### **Merge Conflicts**
```bash
# Durante rebase
git status
# Editar arquivos conflitantes
git add arquivo-resolvido
git rebase --continue

# Durante merge
git status
# Editar arquivos conflitantes  
git add arquivo-resolvido
git commit
```

### **Prevenção**
- Rebases frequentes com `main`
- Commits pequenos e focados
- Comunicação no Discord/Slack
- Review de código antes do merge

---

## ⚡ Setup de Desenvolvimento

### **Ferramentas Recomendadas**
- **IDE**: VS Code ou PyCharm
- **Git GUI**: GitHub Desktop ou GitKraken
- **Comunicação**: Discord/Slack
- **Project Management**: GitHub Projects

### **Extensões VS Code**
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint", 
    "ms-python.black-formatter",
    "eamodio.gitlens",
    "github.vscode-pull-request-github"
  ]
}
```

### **Scripts Úteis**
```bash
# Executar frontend
cd src && python main_frontend.py

# Executar aplicação completa
cd src && python main.py

# Executar testes
python -m pytest tests/

# Formatar código
black src/
```

---

## 🧪 Testes e Qualidade

### **Antes de Cada PR**
```bash
# Executar testes
python -m pytest

# Verificar linting
pylint src/

# Formatar código
black src/

# Executar aplicação
python src/main_frontend.py
```

### **Critérios de Aceitação**
- [ ] Código passa em todos os testes
- [ ] Sem erros de linting
- [ ] Interface responsiva
- [ ] Compatível com Windows 11
- [ ] Documentação atualizada

---

---

## 🚀 Deploy e Entrega

### **Branch `main`**
- Sempre deployável
- Versionamento semântico
- Tags para releases

### **Preparação para Hackathon**
```bash
# Release final
git checkout main
git tag v1.0.0-hackathon
git push origin v1.0.0-hackathon

# Build executável
python scripts/build.py
```

