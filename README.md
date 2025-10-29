# ⚡ Analisador de Tarifários de Eletricidade PT para Home Assistant

[![versão](https://img.shields.io/badge/vers%C3%A3o-3.0.0-blue.svg)](https://github.com/lui54lb3rt0/hass_electricity_best_tarif_PT)
[![hacs_badge](https://img.shields.io/badge/HACS-Personalizado-orange.svg)](https://github.com/custom-components/hacs)
[![Licença](https://img.shields.io/github/license/lui54lb3rt0/hass_electricity_best_tarif_PT.svg)](LICENSE)

> 🇵🇹 **Integração inteligente para análise e recomendação dos melhores tarifários de eletricidade portugueses**

**🆕 NOVA VERSÃO 3.0** - Agora com análise inteligente de consumo personalizada, similar ao que a Octopus Energy faz no Reino Unido!

Integração avançada que não só liga o Home Assistant aos dados oficiais da **ERSE**, mas também analisa o seu padrão de consumo real para recomendar o tarifário ideal para o seu perfil energético.

## ✨ Funcionalidades Principais

### 🧠 **Análise Inteligente de Consumo** (NOVO!)
- **Análise de padrões**: Estuda o seu histórico de consumo energético
- **Períodos tarifários**: Identifica consumo em horas de ponta, cheias e vazio
- **Perfil personalizado**: Cria um perfil único baseado nos seus hábitos
- **Previsões precisas**: Estima custos reais para cada tarifário disponível

### 🏆 **Sistema de Recomendação** (NOVO!)
- **Melhor tarifário**: Identifica automaticamente a opção mais económica
- **Poupanças potenciais**: Calcula quanto pode poupar anualmente
- **Comparação inteligente**: Compara a sua tarifa atual com as melhores opções
- **Alertas de mudança**: Notifica quando encontra melhores oportunidades

### 📊 **Dashboard Interativo** (NOVO!)
- **Cartões personalizados**: Templates prontos para dashboard
- **Gráficos de consumo**: Visualiza padrões por hora, dia e período tarifário
- **Tabelas de comparação**: Rankings de tarifários ordenados por custo
- **Indicadores de poupança**: Métricas visuais de potencial de economia

### 🔄 **Funcionalidades Tradicionais Melhoradas**
- **Sincronização automática**: Dados sempre atualizados da ERSE
- **Filtros avançados**: Por tipo de energia, potência e comercializador
- **Múltiplos sensores**: Sensores tradicionais + sensores de análise
- **Interface nativa**: Configuração através da interface gráfica

## 🚀 Instalação

### Método 1: HACS (Recomendado)
1. **Adicionar repositório personalizado**:
   - HACS → Integrações → ⋮ → Repositórios personalizados
   - URL: `https://github.com/lui54lb3rt0/hass_electricity_best_tarif_PT`
   - Categoria: Integração

2. **Instalar**:
   - HACS → Integrações → Procurar "Analisador Tarifários Eletricidade PT"
   - Transferir e reiniciar o Home Assistant

### Método 2: Instalação Manual
1. **Transferir ficheiros**:
   ```bash
   cd /config/custom_components
   git clone https://github.com/lui54lb3rt0/hass_electricity_best_tarif_PT.git hass_electricity_best_tarif_pt
   ```

2. **Estrutura de ficheiros**:
   ```
   custom_components/hass_electricity_best_tarif_pt/
   ├── __init__.py
   ├── manifest.json
   ├── const.py
   ├── config_flow.py
   ├── sensor.py
   ├── enhanced_sensor.py       # NOVO: Sensores de análise
   ├── consumption_analyzer.py  # NOVO: Motor de análise
   ├── cost_calculator.py      # NOVO: Calculadora de custos
   ├── recommendation_engine.py # NOVO: Sistema de recomendação
   ├── data_loader.py
   └── downloader.py
   ```

3. **Reiniciar o Home Assistant**

## ⚙️ Configuração

### Configuração Básica (Tradicional)
1. **Adicionar Integração**:
   - Definições → Dispositivos e Serviços → Adicionar Integração
   - Procurar "Analisador Tarifários Eletricidade PT"

2. **Configurar Parâmetros Básicos**:
   - **Comercializador**: Escolha o fornecedor de energia
   - **Tipo de Energia**: Eletricidade, Gás Natural, Dual ou Todos
   - **Potência Contratada**: A sua potência contratada (ex: 5.75 kVA)
   - **Códigos de Oferta**: (Opcional) Limitar a ofertas específicas

### 🧠 Configuração Inteligente (NOVO!)
Para ativar a análise personalizada de consumo:

1. **Ativar Análise de Consumo**: Marcar a opção na configuração inicial

2. **Configurar Análise**:
   - **Sensor de Energia**: Escolher o sensor que mede o seu consumo (kWh)
   - **Período de Análise**: Número de dias de histórico a analisar (7-365)
   - **Tipo de Tarifa**: Bi-horário ou Tri-horário
   - **Tarifa Atual**: (Opcional) Código da sua tarifa atual para comparação

### 📊 Resultado da Configuração

#### Sensores Tradicionais:
- **Um sensor por oferta tarifária** (ex: `sensor.edp_tarifa_residencial`)
- **Estado**: Termo fixo diário (€/dia)
- **Atributos**: Todas as condições comerciais

#### 🆕 Sensores de Análise Inteligente:
- **`sensor.consumption_analysis_[sensor]`**: Padrão de consumo analisado
- **`sensor.best_tariff_recommendation`**: Melhor tarifário recomendado  
- **`sensor.potential_annual_savings`**: Poupança potencial anual
- **`sensor.tariff_comparison`**: Comparação detalhada de tarifários

## 📊 Dashboard e Visualizações (NOVO!)

### 🎨 Templates Prontos
A integração inclui templates de dashboard prontos a usar na pasta `/examples/`:

- **`tariff_recommendation_card.yaml`**: Cartão principal com recomendação e métricas
- **`consumption_analysis_card.yaml`**: Análise detalhada de padrões de consumo  
- **`tariff_comparison_table.yaml`**: Tabela comparativa de todos os tarifários
- **`savings_overview_card.yaml`**: Visão geral de poupanças e impacto financeiro
- **`complete_dashboard.yaml`**: Dashboard completo com todas as funcionalidades

### 🚀 Configuração Rápida do Dashboard
1. **Copiar templates**: Usar os ficheiros da pasta `examples/`
2. **Personalizar entity IDs**: Substituir pelos seus sensores reais
3. **Instalar dependências**: Cards personalizados necessários (ver secção abaixo)

### 📦 Cards Recomendados (HACS)
Para a melhor experiência visual, instale estes cards personalizados:
```
- mushroom-cards
- apexcharts-card  
- auto-entities
- stack-in-card
- bar-card
- gauge-card
```

### 💡 Exemplos de Utilização

#### **Cartão de Recomendação Básico**
```yaml
type: custom:mushroom-template-card
primary: "🏆 {{ state_attr('sensor.best_tariff_recommendation', 'recommended_tariff_name') }}"
secondary: "Poupança: €{{ states('sensor.potential_annual_savings') }}/ano"
icon: mdi:lightning-bolt
icon_color: green
```

#### **Gráfico de Consumo por Períodos**
```yaml
type: custom:apexcharts-card
chart_type: donut
series:
  - entity: sensor.consumption_analysis_energy
    attribute: peak_percentage
    name: "Horas de Ponta"
  - entity: sensor.consumption_analysis_energy  
    attribute: off_peak_percentage
    name: "Horas de Vazio"
```

## 📈 Dados e Sensores

### Estado dos Sensores
- **Estado**: Timestamp da última sincronização (formato ISO8601 UTC)
- **Nome**: Nome comercial da oferta (ex: "ENI Plenitude Regime Especial")
- **ID único**: Baseado no código da oferta para evitar duplicação

### Atributos Disponíveis (Exemplos)
```yaml
# Informações básicas
codigo_original: "ENIPLENITUDE_01"
nomeproposta: "ENI Plenitude Regime Especial"
comercializador: "ENI Plenitude"
escalao: "1"

# Condições comerciais
termo_fixo_power: "5.95"  # €/kW/mês
energia_vazio_normal: "0.1425"  # €/kWh
energia_ponta: "0.2156"  # €/kWh
energia_cheia: "0.1598"  # €/kWh

# Metadados
potencia_norm: "5.75"
last_refresh_iso: "2025-10-07T11:00:00Z"
ciclo_faturacao: "Mensal, Bimestral"
```

### Utilização em Modelos e Automatizações

#### **💡 Modelo Básico**
```yaml
# Estado (última atualização)
{{ states('sensor.eni_plenitude_regime_especial') }}

# Preço da energia no vazio normal
{{ state_attr('sensor.eni_plenitude_regime_especial', 'energia_vazio_normal') }} €/kWh

# Nome comercial
{{ state_attr('sensor.eni_plenitude_regime_especial', 'nomeproposta') }}
```

#### **📈 Comparação de Tarifários**
```yaml
# Modelo para encontrar a tarifa mais barata no vazio normal
{% set ns = namespace(min_price=999, best_tariff="") %}
{% for state in states.sensor %}
  {% if 'tarifarios_eletricidade' in state.entity_id %}
    {% set price = state.attributes.energia_vazio_normal | float(999) %}
    {% if price < ns.min_price %}
      {% set ns.min_price = price %}
      {% set ns.best_tariff = state.attributes.nomeproposta %}
    {% endif %}
  {% endif %}
{% endfor %}
Melhor tarifa: {{ ns.best_tariff }} ({{ ns.min_price }} €/kWh)
```

#### **🔔 Automatização de Notificação**
```yaml
automation:
  - alias: "Notificar Atualização Tarifários"
    trigger:
      platform: state
      entity_id: sensor.eni_plenitude_regime_especial
    action:
      service: notify.mobile_app
      data:
        title: "Tarifários Atualizados"
        message: >
          Nova atualização dos tarifários às 
          {{ trigger.to_state.state | as_timestamp | timestamp_custom('%H:%M') }}
```

## 🛠️ Funcionalidades Avançadas

### Atualização Automática
- **Horário**: Diariamente às 11:00 (hora local)
- **Processo**:
  1. Análise da página oficial da ERSE
  2. Descoberta automática dos URLs dos ficheiros CSV
  3. Transferência dos ficheiros atualizados
  4. Processamento e aplicação de filtros
  5. Atualização dos sensores existentes

### Sistema de Registos
```yaml
# configuration.yaml - Para diagnóstico
logger:
  default: warning
  logs:
    custom_components.hass_tarifarios_eletricidade_pt: debug
    custom_components.hass_tarifarios_eletricidade_pt.downloader: info
```

### Recarregamento da Integração
- **Sem perda de dados**: Recarregar mantém o histórico
- **Novos códigos**: Adicionar códigos requer recarregamento
- **Configuração**: Alterações aplicadas imediatamente

## 🔧 Resolução de Problemas

### Problemas Comuns

| 🚨 Problema | 🔍 Causa Provável | ✅ Solução |
|-------------|-------------------|------------|
| **Poucos ou nenhuns sensores** | Filtro de potência incorreto | Verificar formato: usar `.` em vez de `,` |
| **Aviso "blocking I/O"** | Versão desatualizada | Atualizar para versão 2.4.0+ |
| **Sensores não atualizam** | Timezone incorreto | Confirmar configuração de timezone no HA |
| **Erro de download** | Conexão à ERSE falhada | Verificar conectividade à internet |
| **Múltiplos sensores por oferta** | Versão antiga | Atualizar - versão atual agrupa por oferta |

### Diagnóstico Avançado

#### **📋 Verificar Registos de Diagnóstico**
```yaml
# Ativar registos detalhados
logger:
  logs:
    custom_components.hass_tarifarios_eletricidade_pt: debug
```

#### **🔍 Verificar Estado da Integração**
```yaml
# Modelo para verificar a última atualização
{{ state_attr('sensor.nome_da_sua_tarifa', 'last_refresh_iso') }}

# Verificar se os dados estão atualizados (menos de 25 horas)
{{ (now() - states.sensor.nome_da_sua_tarifa.last_updated).total_seconds() < 90000 }}
```

#### **⚡ Forçar Atualização Manual**
1. Ir a Ferramentas de Programador → Serviços
2. Executar: `homeassistant.reload_config_entry`
3. Selecionar a integração "Tarifários Eletricidade PT"

### Perguntas Frequentes (FAQ)

**P: Posso adicionar novos códigos de oferta sem reconfigurar?**
R: Atualmente é necessário recarregar a integração. A funcionalidade de adição dinâmica está no plano de desenvolvimento.

**P: Os preços incluem taxas e impostos?**
R: Os dados vêm diretamente da ERSE e incluem todos os componentes oficiais do tarifário.

**P: Com que frequência os dados da ERSE são atualizados?**
R: A ERSE atualiza os dados conforme necessário. A integração verifica diariamente.

## 📈 Plano de Desenvolvimento e Funcionalidades Futuras

### ✅ Implementado (v2.5.0)
- ✅ Sincronização automática diária
- ✅ Descoberta inteligente de URLs
- ✅ Sistema robusto de redundância  
- ✅ Agregação por oferta (uma entidade por tarifa)
- ✅ Logótipo e controlo de versões profissional
- ✅ Processamento assíncrono completo
- ✅ **Seleção de tipo de energia** (Eletricidade, Gás Natural, Dual, Todos)
- ✅ **Filtros flexíveis** para diferentes necessidades energéticas

### 🔄 Em Desenvolvimento
- 🔄 Adição dinâmica de ofertas sem recarregamento
- 🔄 Métricas derivadas (comparação automática)
- 🔄 Alertas de mudanças de preços
- 🔄 Painel de controlo pré-configurado

### 🎯 Planeado
- 🎯 Suporte para tarifários de gás natural
- 🎯 Histórico de preços e tendências
- 🎯 Integração com painéis solares
- 🎯 API para outras integrações

## 🤝 Contribuir

### Como Contribuir
1. **Fork** do repositório
2. **Clonar** localmente: `git clone https://github.com/SEU_UTILIZADOR/hass_tarifarios_eletricidade_PT.git`
3. **Branch** para funcionalidade: `git checkout -b funcionalidade/nova-funcionalidade`
4. **Commit** das alterações: `git commit -m "Adicionar nova funcionalidade"`
5. **Push**: `git push origin funcionalidade/nova-funcionalidade`
6. **Pull Request** no GitHub

### Estrutura do Projeto
```
├── custom_components/hass_tarifarios_eletricidade_pt/
│   ├── __init__.py           # Inicialização da integração
│   ├── manifest.json         # Metadados e dependências
│   ├── const.py             # Constantes e configuração
│   ├── config_flow.py       # Interface de configuração
│   ├── sensor.py            # Entidades sensor
│   ├── data_loader.py       # Processamento de dados
│   └── downloader.py        # Transferência e descoberta de URLs
├── README.md                # Esta documentação
├── CHANGELOG.md            # Histórico de versões
└── LICENSE                 # Licença MIT
```

## 📄 Licença e Informações Legais

### Licença
Este projeto está licenciado sob a **Licença MIT** - consulte [LICENSE](LICENSE) para mais detalhes.

### Aviso Legal
- **Dados oficiais**: Esta integração utiliza dados públicos disponibilizados pela ERSE
- **Não oficial**: Não tem afiliação oficial com a ERSE ou outras entidades reguladoras
- **Utilização**: Destinado a fins informativos e domésticos
- **Responsabilidade**: Os utilizadores são responsáveis pela verificação independente dos dados

### Controlo de Versões Semântico
Esta integração segue o [Controlo de Versões Semântico 2.0.0](https://semver.org/):
- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Funcionalidades novas compatíveis
- **PATCH**: Correções de erros compatíveis

---

<div align="center">

**🇵🇹 Feito com ❤️ para a comunidade portuguesa do Home Assistant**

[![GitHub stars](https://img.shields.io/github/stars/lui54lb3rt0/hass_tarifarios_eletricidade_PT.svg?style=social&label=Estrela)](https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT)
[![GitHub forks](https://img.shields.io/github/forks/lui54lb3rt0/hass_tarifarios_eletricidade_PT.svg?style=social&label=Fork)](https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/fork)

[📖 Documentação](README.md) • [🐛 Reportar Erro](https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/issues) • [💡 Sugerir Funcionalidade](https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/issues) • [💬 Discussões](https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/discussions)

</div>