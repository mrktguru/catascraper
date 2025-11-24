# 🤖 AI Integration Guide for Wine Rating

## 📋 Обзор

Добавление AI оценки вин в n8n workflow для автоматической оценки по 5 критериям:
- **Producer Rating** (Оценка производителя) - 1-10
- **Vintage Rating** (Оценка винтажа) - 1-10
- **Region Rating** (Оценка региона) - 1-10
- **Overall Appeal** (Общая привлекательность) - 1-10
- **Investment Potential** (Инвестиционная привлекательность) - 1-10

---

## 🔧 Шаг 1: Добавить AI Node в n8n Workflow

### 1.1 Откройте workflow в n8n

### 1.2 Добавьте новую ноду между "Format Results" и "Write to Google Sheets"

**Позиция:** После ноды "Format Results", перед "Write to Google Sheets"

### 1.3 Выберите тип ноды:

**Вариант A: OpenAI** (если используете OpenAI API)
- Нода: **"OpenAI"**
- Model: `gpt-4` или `gpt-3.5-turbo`

**Вариант B: Anthropic Claude** (если используете Claude API)
- Нода: **"Anthropic"**
- Model: `claude-3-5-sonnet-20241022`

**Вариант C: HTTP Request** (для любого другого AI API)
- Нода: **"HTTP Request"**

---

## 🎯 Шаг 2: Настройка AI Node

### Для OpenAI Node:

**Parameters:**
- **Resource**: `Message`
- **Operation**: `Create`
- **Model**: `gpt-4` или `gpt-3.5-turbo`
- **Messages**:

**System Message:**
```
You are a professional wine expert and investment advisor. Analyze wine auction listings and provide ratings on a scale of 1-10.

Your task is to evaluate each wine based on:
1. Producer reputation and quality
2. Vintage quality and aging potential
3. Region prestige and terroir
4. Overall market appeal
5. Investment potential

Return ONLY a JSON object with ratings in this exact format:
{
  "producer_rating": "X/10",
  "vintage_rating": "X/10",
  "region_rating": "X/10",
  "overall_appeal": "X/10",
  "investment_potential": "X/10"
}

Do not include any explanations, only the JSON.
```

**User Message:**
```
{{ $json.title }}
Seller: {{ $json.seller_name }}
Price: {{ $json.current_price }}
Bottles: {{ $json.bottles_count }}
```

**Options:**
- **Response Format**: `json_object`
- **Temperature**: `0.3`
- **Max Tokens**: `150`

---

### Для Anthropic Claude Node:

**Parameters:**
- **Model**: `claude-3-5-sonnet-20241022`

**Prompt:**
```
<instructions>
You are a professional wine expert. Analyze this wine listing and provide ratings 1-10.

Return ONLY valid JSON in this exact format:
{
  "producer_rating": "X/10",
  "vintage_rating": "X/10",
  "region_rating": "X/10",
  "overall_appeal": "X/10",
  "investment_potential": "X/10"
}
</instructions>

<wine_listing>
Title: {{ $json.title }}
Seller: {{ $json.seller_name }}
Price: {{ $json.current_price }}
Bottles: {{ $json.bottles_count }}
</wine_listing>

Respond with ONLY the JSON object, no other text.
```

**Options:**
- **Temperature**: `0.3`
- **Max Tokens**: `150`

---

## 🔄 Шаг 3: Добавить Code Node для парсинга AI ответа

Добавьте **Code Node** сразу после AI Node.

**Name:** "Parse AI Ratings"

**Code:**
```javascript
// Parse AI response and merge with wine data
const items = [];

for (const item of $input.all()) {
  const wineData = item.json;

  // Get AI response
  let aiResponse = {};

  try {
    // For OpenAI
    if (wineData.choices && wineData.choices[0]) {
      aiResponse = JSON.parse(wineData.choices[0].message.content);
    }
    // For Anthropic
    else if (wineData.content && wineData.content[0]) {
      aiResponse = JSON.parse(wineData.content[0].text);
    }
    // For direct JSON response
    else if (typeof wineData === 'object') {
      aiResponse = wineData;
    }
  } catch (error) {
    console.error('Failed to parse AI response:', error);
    // Default values if parsing fails
    aiResponse = {
      producer_rating: "N/A",
      vintage_rating: "N/A",
      region_rating: "N/A",
      overall_appeal: "N/A",
      investment_potential: "N/A"
    };
  }

  // Merge original data with AI ratings
  items.push({
    json: {
      ...item.json,
      producer_rating: aiResponse.producer_rating || "N/A",
      vintage_rating: aiResponse.vintage_rating || "N/A",
      region_rating: aiResponse.region_rating || "N/A",
      overall_appeal: aiResponse.overall_appeal || "N/A",
      investment_potential: aiResponse.investment_potential || "N/A"
    }
  });
}

return items;
```

---

## 📊 Шаг 4: Обновить Google Sheets

### 4.1 Добавьте колонки в лист "Results":

Обновите заголовки:
```
| title | bottles_count | seller_name | current_price | shipping_cost | end_date | images_count | first_image | url | scraped_at | producer_rating | vintage_rating | region_rating | overall_appeal | investment_potential |
```

### 4.2 Настройки Write to Google Sheets уже обновлены ✅

Новые колонки уже добавлены в workflow:
- `producer_rating`
- `vintage_rating`
- `region_rating`
- `overall_appeal`
- `investment_potential`

---

## 🔗 Шаг 5: Обновить связи в Workflow

Измените связи нод:

**Старая структура:**
```
Format Results → Write to Google Sheets
```

**Новая структура:**
```
Format Results → AI Agent (OpenAI/Anthropic) → Parse AI Ratings → Write to Google Sheets
```

---

## 🧪 Шаг 6: Тестирование

### 6.1 Тестовый запуск:

1. Откройте workflow
2. Нажмите "Execute Workflow"
3. Проверьте вывод каждой ноды:
   - **Format Results** → должны быть данные о вине
   - **AI Agent** → должен вернуть JSON с оценками
   - **Parse AI Ratings** → данные + AI оценки вместе
   - **Write to Google Sheets** → запись в таблицу

### 6.2 Проверьте Google Sheets:

Новые колонки должны содержать значения типа:
- `8/10`
- `9/10`
- `7/10`

---

## 💡 Примеры AI оценок

**Пример хорошего вина:**
```json
{
  "producer_rating": "9/10",
  "vintage_rating": "8/10",
  "region_rating": "9/10",
  "overall_appeal": "9/10",
  "investment_potential": "8/10"
}
```

**Пример среднего вина:**
```json
{
  "producer_rating": "6/10",
  "vintage_rating": "5/10",
  "region_rating": "7/10",
  "overall_appeal": "6/10",
  "investment_potential": "4/10"
}
```

---

## 🔐 API Keys

### OpenAI:
1. Получите API key: https://platform.openai.com/api-keys
2. В n8n: **Credentials** → **OpenAI** → добавьте API key

### Anthropic Claude:
1. Получите API key: https://console.anthropic.com/
2. В n8n: **Credentials** → **Anthropic** → добавьте API key

---

## 💰 Стоимость API вызовов

### OpenAI GPT-4:
- Input: ~$0.03 на 1K токенов
- Output: ~$0.06 на 1K токенов
- **~$0.01 на одно вино**

### OpenAI GPT-3.5-turbo:
- Input: ~$0.0005 на 1K токенов
- Output: ~$0.0015 на 1K токенов
- **~$0.0005 на одно вино**

### Anthropic Claude 3.5 Sonnet:
- Input: ~$0.003 на 1K токенов
- Output: ~$0.015 на 1K токенов
- **~$0.002 на одно вино**

**Рекомендация:** Для продакшена используйте GPT-3.5-turbo (дешевле) или Claude Haiku.

---

## 🚨 Troubleshooting

### Проблема: AI возвращает текст вместо JSON

**Решение:**
- Для OpenAI: добавьте `Response Format: json_object`
- Для Claude: обновите промпт, добавьте `<response_format>json</response_format>`

### Проблема: Parse AI Ratings выдает ошибку

**Решение:**
- Проверьте вывод AI Node
- Убедитесь что JSON валидный
- Добавьте `console.log()` в Code Node для отладки

### Проблема: Google Sheets показывает "N/A"

**Решение:**
- Проверьте что Parse AI Ratings успешно парсит JSON
- Проверьте что имена полей совпадают точно

---

## 📝 Примечания

- AI оценка происходит **после** парсинга, перед записью в Google Sheets
- Каждое вино оценивается индивидуально
- Если AI недоступен, будет записано "N/A"
- Temperature 0.3 дает более стабильные оценки
- Для batch обработки AI вызывается для каждого вина отдельно

---

## ✅ Готово!

После настройки workflow будет:
1. Парсить данные с Catawiki
2. Отправлять каждое вино в AI для оценки
3. Получать 5 рейтингов (X/10)
4. Записывать всё в Google Sheets

**Результат в Google Sheets:**
```
| Title | ... | Producer Rating | Vintage Rating | Region Rating | Overall Appeal | Investment Potential |
|-------|-----|-----------------|----------------|---------------|----------------|---------------------|
| 1989 Veuve Clicquot | ... | 9/10 | 8/10 | 9/10 | 9/10 | 8/10 |
```
