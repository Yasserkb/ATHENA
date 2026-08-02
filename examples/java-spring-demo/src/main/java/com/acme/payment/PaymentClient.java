package com.acme.payment;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class PaymentClient {
    private final String baseUrl;

    public PaymentClient(@Value("${payment.client.base-url}") String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public String authorize(long amount) {
        return "auth-" + amount;
    }
}
