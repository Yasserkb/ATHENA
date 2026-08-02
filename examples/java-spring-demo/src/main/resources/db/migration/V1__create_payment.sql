CREATE TABLE payment (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(100) NOT NULL,
    amount BIGINT NOT NULL
);
