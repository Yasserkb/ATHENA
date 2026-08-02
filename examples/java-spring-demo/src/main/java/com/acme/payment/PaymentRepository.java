package com.acme.payment;

import org.springframework.stereotype.Repository;

@Repository
public interface PaymentRepository {
    Payment save(Payment payment);
}
