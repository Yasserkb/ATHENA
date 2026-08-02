export class CheckoutService {
  submit(orderId: string): string {
    return `submitted:${orderId}`;
  }
}
