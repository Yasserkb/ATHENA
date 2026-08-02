package com.acme.payment;

import org.springframework.stereotype.Service;

@Service
public class PaymentService {
    private final PaymentRepository paymentRepository;
    private final PaymentClient paymentClient;

    public PaymentService(PaymentRepository paymentRepository, PaymentClient paymentClient) {
        this.paymentRepository = paymentRepository;
        this.paymentClient = paymentClient;
    }

    public PaymentResponse create(PaymentRequest request) {
        String externalId = paymentClient.authorize(request.amount());
        Payment payment = paymentRepository.save(new Payment(externalId, request.amount()));
        return new PaymentResponse(payment.externalId());
    }
}
