// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Component, OnInit, ChangeDetectionStrategy, HostListener, ViewChildren, QueryList, ElementRef, inject } from '@angular/core';
import { CommonModule, AsyncPipe } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Observable } from 'rxjs';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-order-management',
  standalone: true,
  imports: [
    CommonModule,
    AsyncPipe,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatButtonModule,
    MatTableModule,
    MatIconModule
  ],
  template: `
    <div class="order-management-container" role="region" aria-label="Order management">
      <mat-card class="order-card">
        <mat-card-header>
          <mat-card-title>Place New Order</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <form [formGroup]="orderForm" aria-label="Order form" (keydown)="onFormKeyDown($event)">
            <div class="form-field" *ngFor="let field of formFields; let i = index" [attr.data-index]="i">
              <mat-form-field appearance="fill">
                <mat-label>{{field.label}}</mat-label>
                <mat-select *ngIf="field.type === 'select'" [formControlName]="field.name" [attr.aria-label]="field.ariaLabel">
                  <mat-option *ngFor="let option of field.options" [value]="option.value">{{option.label}}</mat-option>
                </mat-select>
                <input *ngIf="field.type === 'number'" matInput type="number" [formControlName]="field.name"
                                   [attr.aria-label]="field.ariaLabel" [min]="field.min || 0" [step]="field.step || 1">
              </mat-form-field>
            </div>

            <button mat-raised-button color="primary" type="submit" [disabled]="!orderForm.valid"
                    aria-label="Submit order" #submitButton>
              Place Order
            </button>
          </form>
        </mat-card-content>
      </mat-card>

      <mat-card class="open-orders-card">
        <mat-card-header>
          <mat-card-title>Open Orders</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="table-container">
            <table mat-table [dataSource]="(openOrders$ | async) || []" aria-label="Open orders table">
              <ng-container matColumnDef="symbol">
                <th mat-header-cell *matHeaderCellDef>Symbol</th>
                <td mat-cell *matCellDef="let order">{{order.symbol}}</td>
              </ng-container>

              <ng-container matColumnDef="type">
                <th mat-header-cell *matHeaderCellDef>Type</th>
                <td mat-cell *matCellDef="let order">{{order.type}}</td>
              </ng-container>

              <ng-container matColumnDef="volume">
                <th mat-header-cell *matHeaderCellDef>Volume</th>
                <td mat-cell *matCellDef="let order">{{order.volume}}</td>
              </ng-container>

              <ng-container matColumnDef="price">
                <th mat-header-cell *matHeaderCellDef>Price</th>
                <td mat-cell *matCellDef="let order">{{order.price}}</td>
              </ng-container>

              <ng-container matColumnDef="actions">
                <th mat-header-cell *matHeaderCellDef>Actions</th>
                <td mat-cell *matCellDef="let order; let i = index">
                  <button mat-icon-button color="warn" [attr.aria-label]="'Cancel order ' + order.id"
                          (click)="cancelOrder(order)" (keydown)="onCancelKeyDown($event, i)" #cancelButtons>
                    <mat-icon>cancel</mat-icon>
                  </button>
                </td>
              </ng-container>

              <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
              <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
            </table>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styleUrls: ['./order-management.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class OrderManagementComponent implements OnInit {
  orderForm: FormGroup = new FormGroup({});
  openOrders$: Observable<any[]> = new Observable<any[]>();
  displayedColumns: string[] = ['symbol', 'type', 'volume', 'price', 'actions'];
  currentFieldIndex = 0;

  @ViewChildren('submitButton') submitButtons: QueryList<ElementRef> = new QueryList<ElementRef>();
  @ViewChildren('cancelButtons') cancelButtons: QueryList<ElementRef> = new QueryList<ElementRef>();

  private fb = inject(FormBuilder);

  formFields: Array<{
    name: string;
    label: string;
    type: string;
    ariaLabel: string;
    options?: Array<{value: string; label: string}>;
    min?: number;
    step?: number
  }> = [
    {
      name: 'symbol',
      label: 'Symbol',
      type: 'select',
      ariaLabel: 'Select trading symbol',
      options: [
        { value: 'XAUUSD', label: 'Gold (XAUUSD)' },
        { value: 'EURUSD', label: 'EUR/USD' },
        { value: 'GBPUSD', label: 'GBP/USD' }
      ]
    },
    {
      name: 'orderType',
      label: 'Order Type',
      type: 'select',
      ariaLabel: 'Select order type',
      options: [
        { value: 'market', label: 'Market' },
        { value: 'limit', label: 'Limit' },
        { value: 'stop', label: 'Stop' }
      ]
    },
    {
      name: 'volume',
      label: 'Volume',
      type: 'number',
      ariaLabel: 'Order volume',
      min: 0.01,
      step: 0.01
    },
    {
      name: 'price',
      label: 'Price',
      type: 'number',
      ariaLabel: 'Order price',
      min: 0,
      step: 0.01
    }
  ];

  constructor() {}

  ngOnInit(): void {
    this.orderForm = this.fb.group({
      symbol: ['XAUUSD', Validators.required],
      orderType: ['market', Validators.required],
      volume: [0.1, [Validators.required, Validators.min(0.01)]],
      price: [{value: null, disabled: true}]
    });

    this.orderForm.get('orderType')?.valueChanges.subscribe(type => {
      if (type === 'market') {
        this.orderForm.get('price')?.disable();
      } else {
        this.orderForm.get('price')?.enable();
      }
    });
  }

  onFormKeyDown(event: KeyboardEvent): void {
    // Handle Enter key to submit form
    if (event.key === 'Enter' && this.orderForm.valid) {
      event.preventDefault();
      this.onSubmit();
      return;
    }

    // Handle arrow keys for navigation between form fields
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      this.currentFieldIndex = (this.currentFieldIndex + 1) % this.formFields.length;
      this.focusFormField(this.currentFieldIndex);
    }
    else if (event.key === 'ArrowUp') {
      event.preventDefault();
      this.currentFieldIndex = (this.currentFieldIndex - 1 + this.formFields.length) % this.formFields.length;
      this.focusFormField(this.currentFieldIndex);
    }
    else if (event.key === 'Tab' && !event.shiftKey && this.currentFieldIndex === this.formFields.length - 1) {
      // Handle Tab from last field to submit button
      event.preventDefault();
      this.submitButtons.first.nativeElement.focus();
    }
    else if (event.key === 'Tab' && event.shiftKey && this.submitButtons.first.nativeElement === document.activeElement) {
      // Handle Shift+Tab from submit button to last field
      event.preventDefault();
      this.currentFieldIndex = this.formFields.length - 1;
      this.focusFormField(this.currentFieldIndex);
    }
  }

  onCancelKeyDown(event: KeyboardEvent, buttonIndex: number): void {
    // Handle Enter or Space on cancel buttons
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      const cancelButtonArray = this.cancelButtons.toArray();
      if (cancelButtonArray[buttonIndex]) {
        const buttonElement = cancelButtonArray[buttonIndex].nativeElement as HTMLElement;
        buttonElement.click();
      }
    }
  }

  onSubmit(): void {
    if (this.orderForm.valid) {
      // TODO: Implement order submission logic
      console.log('Order submitted:', this.orderForm.value);
    }
  }

  cancelOrder(order: any): void {
    console.log('Cancel order:', order);
    // TODO: Implement order cancellation logic
  }

  private focusFormField(index: number): void {
    const formFields = document.querySelectorAll('.form-field');
    if (formFields && formFields[index]) {
      const selectTrigger = formFields[index].querySelector('.mat-select-trigger');
      const input = formFields[index].querySelector('input');

      if (selectTrigger) {
        (selectTrigger as HTMLElement).focus();
      } else if (input) {
        (input as HTMLElement).focus();
      }
    }
  }
}