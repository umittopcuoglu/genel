PRICING = {
    "deepseek": {
        "input": 0.14 / 1_000_000,
        "output": 0.28 / 1_000_000,
    },
    "openai": {
        "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
        "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},
    },
    "claude": {
        "claude-opus-4-1": {"input": 0.015 / 1000, "output": 0.075 / 1000},
    },
}


def calc_cost(
    provider: str, model: str, input_tokens: int, output_tokens: int
) -> float:
    rates = PRICING.get(provider, {})

    if model in rates and isinstance(rates[model], dict):
        # Model-bazlı nested fiyatlandırma (openai, claude)
        model_rates = rates[model]
        input_rate = model_rates.get("input", 0)
        output_rate = model_rates.get("output", 0)
    else:
        # Düz fiyatlandırma (deepseek)
        input_rate = rates.get("input", 0)
        output_rate = rates.get("output", 0)

    input_cost = input_tokens * input_rate
    output_cost = output_tokens * output_rate
    return input_cost + output_cost
